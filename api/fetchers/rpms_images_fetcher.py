import os
import logging

from ghapi.all import GhApi

GITHUB_TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")

REPO_OWNER = "openshift-eng"
REPO_NAME = "ocp-build-data"

api = GhApi(owner=REPO_OWNER, repo=REPO_NAME, token=GITHUB_TOKEN)

# Set up logging
logger = logging.getLogger(__name__)


def get_directory_contents(branch, directory):
    """
    Fetches the contents of a directory in a given branch of the GitHub repository.

    Args:
        branch: The name of the branch.
        directory: The path of the directory.

    Returns:
        The contents of the directory.
    """
    return api.repos.get_content(owner=REPO_OWNER, repo=REPO_NAME, path=directory, ref=branch)


def fetch_data(release):
    """
    Fetches the rpms and images data for a specific release from the GitHub repository.

    Args:
        release: The name of the release (which corresponds to a branch in the repository).

    Returns:
        A list of dictionaries, where each dictionary contains the rpms and images for a branch.
    """
    result = []

    # Directly access the branch for the given release
    rpms_content = get_directory_contents(release, "rpms")
    images_content = get_directory_contents(release, "images")

    rpms = [rpm["name"] for rpm in rpms_content if rpm["type"] == "file"]
    images = [image["name"] for image in images_content if image["type"] == "file"]

    result.append({
        "branch": release,
        "rpms": rpms,
        "images": images,
    })

    return result
