import os
import requests
import logging
import json

# Set your GitHub access token as an environment variable
GITHUB_TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
headers = {
    "Authorization": f"token {GITHUB_TOKEN}"
}

REPO_OWNER = "openshift-eng"
REPO_NAME = "ocp-build-data"

def get_directory_contents(branch, directory):
    path = f"{REPO_OWNER}/{REPO_NAME}/contents/{directory}?ref={branch}"
    contents_api = f"https://api.github.com/repos/{path}"
    response = requests.get(contents_api, headers=headers)
    response.raise_for_status()  # Raise an exception if the request fails
    return response

def fetch_data():
    result = []

    # Separate entry for the "openshift-3.11" branch
    branch_name = "openshift-3.11"
    logging.debug(f"Processing branch {branch_name}...")

    try:
        rpms_content = get_directory_contents(branch_name, "rpms")
        images_content = get_directory_contents(branch_name, "images")

        if rpms_content.status_code == 200 and images_content.status_code == 200:
            rpms = [rpm["name"] for rpm in rpms_content.json() if rpm["type"] == "file"]
            images = [image["name"] for image in images_content.json() if image["type"] == "file"]

            result.append({
                "branch": branch_name,
                "rpms": rpms,
                "images": images,
            })

    except requests.exceptions.HTTPError as e:
        logging.warning(f"Error occurred when fetching data for branch {branch_name}: {e}")

    # Loop for "openshift-4.{i}" branches
    for i in range(5, 15):
        branch_name = f"openshift-4.{i}" 
        logging.debug(f"Processing branch {branch_name}...")

        try:
            rpms_content = get_directory_contents(branch_name, "rpms")
            images_content = get_directory_contents(branch_name, "images")

            if rpms_content.status_code == 200 and images_content.status_code == 200:
                rpms = [rpm["name"] for rpm in rpms_content.json() if rpm["type"] == "file"]
                images = [image["name"] for image in images_content.json() if image["type"] == "file"]

                result.append({
                    "branch": branch_name,
                    "rpms": rpms,
                    "images": images,
                })

        except requests.exceptions.HTTPError as e:
            logging.warning(f"Error occurred when fetching data for branch {branch_name}: {e}")

    return result

result = fetch_data()

result_json = json.dumps(result, indent=2, sort_keys=True)
