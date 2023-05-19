import os

from ghapi.all import GhApi

GITHUB_TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")

REPO_OWNER = "openshift-eng"
REPO_NAME = "ocp-build-data"

api = GhApi(owner=REPO_OWNER, repo=REPO_NAME, token=GITHUB_TOKEN)


def get_directory_contents(branch, directory):
    return api.repos.get_content(owner=REPO_OWNER, repo=REPO_NAME, path=directory, ref=branch)


def fetch_data(release):
    result = []
    branches = api.list_branches()

    for branch in branches:
        branch_ref = branch.ref
        branch_name = branch_ref.split('/')[-1]

        # Check if the branch matches the specified release
        if branch_name != release:
            continue

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
