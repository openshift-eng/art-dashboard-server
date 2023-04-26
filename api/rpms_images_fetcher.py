import os
import re
import logging
import json
from ghapi.all import GhApi

# Set your GitHub access token as an environment variable, e.g., export GITHUB_TOKEN="your_token_here"
GITHUB_TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")

REPO_OWNER = "openshift-eng"
REPO_NAME = "ocp-build-data"

api = GhApi(owner=REPO_OWNER, repo=REPO_NAME, token=GITHUB_TOKEN)

def get_directory_contents(branch, directory):
    return api.repos.get_content(owner=REPO_OWNER, repo=REPO_NAME, path=directory, ref=branch)


def fetch_data():
    result = []
    branches = api.list_branches()
    branch_pattern = re.compile(r'^(openshift-3\.11|openshift-4\.\d+)$')

    for branch in branches:
        branch_ref = branch.ref
        branch_name = branch_ref.split('/')[-1]

        if not branch_pattern.match(branch_name):
            continue

        logging.debug(f"Processing branch {branch_name}...")

        rpms_content = get_directory_contents(branch_name, "rpms")
        images_content = get_directory_contents(branch_name, "images")

        rpms = [rpm["name"] for rpm in rpms_content if rpm["type"] == "file"]
        images = [image["name"] for image in images_content if image["type"] == "file"]

        result.append({
            "branch": branch_name,
            "rpms": rpms,
            "images": images,
        })

    return result

result = fetch_data()

# Convert the result to a JSON formatted string
result_json = json.dumps(result, indent=2, sort_keys=True)
