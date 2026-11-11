"""Read-only product release discovery from build data and shipment MRs."""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import RLock
from urllib.parse import quote

import requests
import yaml
from cachetools import TTLCache, cached

from lib.gitlab_requests import get_shipment_status
from lib.products import PRODUCTS, get_product, validate_product_group, version_key

_metadata_cache = TTLCache(maxsize=128, ttl=120)
_release_cache = TTLCache(maxsize=128, ttl=30)
_cache_lock = RLock()


def _github_headers():
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    return {"Authorization": f"token {token}"} if token else {}


def _build_data_yaml(group, filename, optional=False):
    base = os.environ.get("GITHUB_RAW_CONTENT_URL", "https://raw.githubusercontent.com/openshift/ocp-build-data")
    response = requests.get(f"{base}/{quote(group, safe='')}/{filename}", headers=_github_headers(), timeout=30)
    if optional and response.status_code == 404:
        return {}
    response.raise_for_status()
    data = yaml.safe_load(response.text) or {}
    if not isinstance(data, dict):
        raise TypeError(f"Invalid {filename} for {group}")
    return data


@cached(_metadata_cache, lock=_cache_lock)
def get_product_groups(product_id):
    product = get_product(product_id)
    branches = _build_data_branches()
    prefix = f"{product['group_prefix']}-"
    groups = []
    for branch in branches:
        name = branch.get("name", "")
        if not name.startswith(prefix):
            continue
        try:
            validate_product_group(product_id, name)
        except ValueError:
            continue
        groups.append(name)
    return sorted(groups, key=version_key, reverse=True)


@cached(_metadata_cache, lock=_cache_lock)
def _build_data_branches():
    branches = []
    page = 1
    while True:
        response = requests.get("https://api.github.com/repos/openshift/ocp-build-data/branches",
                                headers=_github_headers(), params={"per_page": 100, "page": page}, timeout=30)
        response.raise_for_status()
        batch = response.json()
        branches.extend(batch)
        if len(batch) < 100:
            return branches
        page += 1


@cached(_metadata_cache, lock=_cache_lock)
def get_product_releases(product_id, group):
    product = validate_product_group(product_id, group)
    config = _build_data_yaml(group, "group.yml")
    if config.get("product", "ocp" if product_id == "openshift" else None) != product["shipment_product"]:
        raise ValueError(f"Unexpected product metadata in {group}/group.yml")
    data = _build_data_yaml(group, "releases.yml", optional=True)
    # Reuse the existing assembly inheritance and merge semantics.
    from lib.http_requests import _assembly_field

    releases = []
    for version, release in (data.get("releases") or {}).items():
        assembly = release.get("assembly") or {}
        if version == "stream" or assembly.get("type", "").lower() == "custom":
            continue
        effective = _assembly_field("group", data, version) or {}
        shipment = effective.get("shipment") or {}
        releases.append({
            "version": version,
            "release_date": effective.get("release_date"),
            "jira": effective.get("release_jira"),
            "shipment_url": shipment.get("mr") or shipment.get("url"),
            "advisories": effective.get("advisories") or {},
        })
    # Older OCP branches predate named release assemblies.
    if not releases and group in ("openshift-3.11", "openshift-4.5") and config.get("advisories"):
        releases.append({"version": "current", "release_date": None, "jira": None,
                         "shipment_url": None, "advisories": config["advisories"]})
    return sorted(releases, key=lambda r: version_key(r["version"]), reverse=True)


@cached(_release_cache, lock=_cache_lock)
def get_product_release(product_id, group, version):
    validate_product_group(product_id, group)
    release = next((r for r in get_product_releases(product_id, group) if r["version"] == version), None)
    if release is None:
        raise LookupError(f"Release {version} is not recorded in {group}")
    result = {**release, "product": product_id, "group": group, "shipments": [], "approvals": {}}
    if release["shipment_url"]:
        shipment = get_shipment_status(release["shipment_url"], group, version)
        if shipment.get("error"):
            # Do not cache failed upstream lookups as a successful release.
            raise requests.RequestException(shipment["error"])
        result.update({key: shipment[key] for key in ("shipments", "approvals", "status", "mr_state", "pipeline")})
    return result


def get_products_overview():
    def summarize(product_id):
        product = get_product(product_id)
        try:
            groups = get_product_groups(product_id)
            # Prefer a group with release entries over a newly bootstrapped empty group.
            for group in groups:
                releases = get_product_releases(product_id, group)
                if releases:
                    return {"product": product, "group": group, "release": get_product_release(product_id, group, releases[0]["version"])}
            return {"product": product, "group": groups[0] if groups else None, "release": None}
        except (requests.RequestException, ValueError, LookupError, TypeError, yaml.YAMLError) as exc:
            return {"product": product, "error": str(exc)}

    with ThreadPoolExecutor(max_workers=3) as pool:
        return list(pool.map(summarize, PRODUCTS))
