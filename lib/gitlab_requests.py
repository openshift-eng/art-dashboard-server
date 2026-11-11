import base64
import hashlib
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus

import requests
import yaml

from lib.products import product_for_group

logger = logging.getLogger(__name__)

GITLAB_API_URL = "https://gitlab.cee.redhat.com/api/v4"


def _get_gitlab_headers():
    token = os.environ.get("GITLAB_API_TOKEN", "")
    return {"PRIVATE-TOKEN": token}


def _parse_mr_url(mr_url):
    """Parse a GitLab MR URL into project path and MR IID."""
    match = re.match(r'https?://[^/]+/(.+?)/-/merge_requests/(\d+)', mr_url)
    if not match:
        return None, None
    return match.group(1), int(match.group(2))


def _gitlab_get(endpoint):
    url = f"{GITLAB_API_URL}/{endpoint}"
    response = requests.get(url, headers=_get_gitlab_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def _get_mr_metadata(project_encoded, iid):
    return _gitlab_get(f"projects/{project_encoded}/merge_requests/{iid}")


def _get_mr_approval_state(project_encoded, iid):
    return _gitlab_get(f"projects/{project_encoded}/merge_requests/{iid}/approval_state")


def _get_file_content(project_encoded, file_path_encoded, ref):
    data = _gitlab_get(f"projects/{project_encoded}/repository/files/{file_path_encoded}?ref={quote_plus(ref)}")
    content = base64.b64decode(data["content"]).decode("utf-8")
    return yaml.safe_load(content)


def _parse_shipment_file(parsed_yaml):
    """Extract advisory data from a parsed shipment YAML file."""
    shipment = parsed_yaml.get("shipment", {})
    data = shipment.get("data") or {}
    environments = shipment.get("environments") or {}
    if not isinstance(data, dict) or not isinstance(environments, dict):
        raise TypeError("Invalid shipment data or environments")
    release_notes = data.get("releaseNotes") or {}
    if not isinstance(release_notes, dict):
        raise TypeError("Invalid shipment release notes")
    stage = _environment_status(environments.get("stage"))
    prod = _environment_status(environments.get("prod"))

    return {
        "type": release_notes.get("type"),
        "live_id": release_notes.get("live_id"),
        "synopsis": release_notes.get("synopsis", ""),
        "stage_url": stage["advisory_url"],
        "prod_url": prod["advisory_url"],
        "stage": stage,
        "prod": prod,
    }


def _get_mr_files(project_encoded, iid):
    """Paginate diffs rather than guessing filenames or application names."""
    files = []
    page = 1
    while True:
        batch = _gitlab_get(f"projects/{project_encoded}/merge_requests/{iid}/diffs?per_page=100&page={page}")
        files.extend(d["new_path"] for d in batch if not d.get("deleted_file"))
        if len(batch) < 100:
            return sorted(set(files))
        page += 1


def _environment_status(environment):
    if not environment:
        return {"status": "Not configured", "advisory_url": None, "pipeline_url": None}
    if not isinstance(environment, dict):
        raise TypeError("Invalid shipment environment metadata")
    advisory = environment.get("advisory") or {}
    result = environment.get("result") or {}
    if not isinstance(advisory, dict) or not isinstance(result, dict):
        raise TypeError("Invalid shipment environment result")
    pipeline = result.get("pipeline")
    if str(environment.get("releasePlan", "")).lower() == "skipped":
        status = "Skipped"
    elif pipeline or advisory.get("url"):
        status = "Succeeded"
    else:
        status = "Not started"
    return {"status": status, "advisory_url": advisory.get("url"), "pipeline_url": pipeline}


def _shipment_summary(shipments, mr_state):
    if not shipments or any(s.get("error") for s in shipments):
        return "Unknown"
    production = [s["prod"]["status"] for s in shipments if s["prod"]["status"] != "Not configured"]
    staging = [s["stage"]["status"] for s in shipments if s["stage"]["status"] != "Not configured"]
    if not production and not staging:
        return "Unknown"
    if production and all(s == "Succeeded" for s in production):
        return "SHIPPED_LIVE"
    if "Succeeded" in production:
        return "Partially shipped"
    if staging and all(s == "Skipped" for s in staging):
        return "Stage skipped"
    if staging and all(s in ("Succeeded", "Skipped") for s in staging):
        return "Staged"
    if "Succeeded" in staging:
        return "Partially staged"
    return "In review" if mr_state == "opened" else "Pending"


def get_shipment_status(mr_url, branch, assembly):
    """
    Get shipment advisory status from a GitLab MR.

    Returns dict with status, approvals, and per-kind advisory data.
    """
    project_path, iid = _parse_mr_url(mr_url)
    if not project_path or not iid:
        return {"error": f"Could not parse MR URL: {mr_url}"}

    project_encoded = quote_plus(project_path)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            future_mr = pool.submit(_get_mr_metadata, project_encoded, iid)
            future_approvals = pool.submit(_get_mr_approval_state, project_encoded, iid)

            mr_data = future_mr.result()
            approval_data = future_approvals.result()
    except (requests.RequestException, ValueError, KeyError, TypeError, yaml.YAMLError) as e:
        logger.error(f"Error fetching MR metadata for {mr_url}: {e}")
        return {"error": str(e)}

    state = mr_data.get("state", "")

    approvals = {}
    for rule in approval_data.get("rules", []):
        rule_name = rule.get("name", "")
        approved_by_list = rule.get("approved_by", [])
        approver_name = ", ".join(user.get("name", "") for user in approved_by_list if user.get("name"))
        approvals[rule_name] = {
            "approved": rule.get("approved", False),
            "approved_by": approver_name,
            "required": rule.get("approvals_required", 1) > 0,
        }

    try:
        product = product_for_group(branch)
        ref = (mr_data.get("merge_commit_sha") or mr_data.get("squash_commit_sha") or mr_data.get("sha")) if state == "merged" else mr_data.get("sha")
        if not ref:
            raise ValueError("The shipment MR has no readable commit revision")
        project = str(mr_data.get("target_project_id") if state == "merged" else mr_data.get("source_project_id") or "")
        if project == "None" or not project:
            project = project_encoded
        prefix = f"shipment/{product['shipment_product']}/{branch}/"
        files = [path for path in _get_mr_files(project_encoded, iid)
                 if path.startswith(prefix) and path.endswith((".yaml", ".yml")) and path.rsplit("/", 1)[-1].startswith(f"{assembly}.")]
        if not files:
            raise ValueError(f"No shipment files found for {branch} / {assembly} in this MR")
    except (requests.RequestException, ValueError, KeyError, TypeError, yaml.YAMLError) as e:
        logger.warning("Could not discover shipment files for %s: %s", mr_url, e)
        return {"error": str(e)}

    def fetch_file(file_path):
        name = file_path.rsplit("/", 1)[-1][len(assembly) + 1:]
        kind = name.split(".")[0]
        try:
            parsed = _get_file_content(project, quote_plus(file_path), ref)
            if not isinstance(parsed, dict) or not isinstance(parsed.get("shipment"), dict):
                raise TypeError("Invalid shipment document")
            metadata = parsed["shipment"]["metadata"]
            if not isinstance(metadata, dict):
                raise TypeError("Invalid shipment metadata")
            expected = {"product": product["shipment_product"], "group": branch, "assembly": assembly}
            if any(metadata.get(key) != value for key, value in expected.items()):
                raise ValueError("Shipment metadata does not match the selected product, group and release")
            path_parts = file_path.split("/")
            if len(path_parts) != 6 or path_parts[3] != metadata.get("application") or path_parts[4] not in ("prod", "stage"):
                raise ValueError("Shipment path does not match its application and environment")
            result = _parse_shipment_file(parsed)
            result.update({"id": file_path, "kind": "fbc" if metadata.get("fbc") else kind,
                           "application": metadata.get("application"), "target_environment": path_parts[4],
                           "advisory_required": metadata.get("advisory_required", True) and not metadata.get("fbc", False)})
            anchor = hashlib.sha1(file_path.encode()).hexdigest()
            result["diff_url"] = f"{mr_url}/diffs#{anchor}"
            return result
        except (requests.RequestException, ValueError, KeyError, TypeError, yaml.YAMLError) as e:
            logger.warning("Could not read shipment file %s: %s", file_path, e)
            return {"id": file_path, "kind": kind, "error": "Could not load shipment details"}

    with ThreadPoolExecutor(max_workers=4) as pool:
        shipments = list(pool.map(fetch_file, files))
    # Keep the original keyed response for existing OpenShift clients.
    advisories = {s["kind"]: s for s in shipments if not s.get("error") and s["kind"] in ("image", "extras", "metadata")}
    pipeline = mr_data.get("head_pipeline") or {}

    return {
        "status": _shipment_summary(shipments, state),
        "mr_url": mr_url,
        "mr_state": state,
        "approvals": approvals,
        "advisories": advisories,
        "shipments": shipments,
        "pipeline": {"status": pipeline.get("status"), "url": pipeline.get("web_url")},
    }
