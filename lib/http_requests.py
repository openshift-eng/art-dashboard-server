"""
This module has helper functions to make http requests to other apis.
"""
import pprint

import requests
import ocp_build_data.constants as app_constants
import lib.constants as constants
import traceback
import os
import yaml
import time
import logging
from urllib.parse import urlparse

HEADERS = {"Authorization": f"token {os.environ['GITHUB_PERSONAL_ACCESS_TOKEN']}"}
logger = logging.getLogger(__name__)


def get_all_ocp_build_data_branches():
    """
    This function lists all the branches of the ocp-build-data repository.
    :return: dict, all the branches along with their details.
    """

    try:
        req = requests.get(app_constants.GITHUB_URL_TO_LIST_ALL_OCP_BUILD_DATA_BRANCHES, headers=HEADERS)
        branches = req.json()

        # Check if multiple pages are present. By default, GitHub API limits to 30 results per page. ocp-build data has
        # a lot of branches.
        # https://docs.github.com/en/rest/branches/branches#list-branches
        while 'next' in req.links.keys():
            req = requests.get(req.links['next']['url'], headers=HEADERS)
            branches.extend(req.json())
        branches_data = []

        for branch in branches:
            if "name" in branch:
                if constants.OCP_BUILD_DATA_RELEVANT_BRANCHES_REGEX_COMPILER.match(branch["name"]):
                    branch_data = dict()
                    branch_data["name"] = branch["name"]
                    version = branch["name"].split("openshift-")[1]
                    branch_data["version"] = version
                    branch_data["priority"] = 0
                    branch_data["extra_details"] = branch
                    branches_data.append(branch_data)
        try:
            branches_data = sorted(branches_data, key=lambda k: (int(float(k["version"])),
                                                                 int(k["version"].split(".")[1])),
                                   reverse=True)
        except Exception:
            print("Something wrong with openshift versions on ocp-build-data branch names.")

        return branches_data

    except Exception:
        traceback.print_exc()
        return []


def get_group_yml_file_url(branch_name: str) -> dict:
    """
    This method takes a branch name of ocp_build_data as a parameter and returns advisories details for the same.
    :param branch_name: Branch name of ocp_build_data
    :return: adivsories details
    """
    hit_url = app_constants.GITHUB_GROUP_YML_CONTENTS_URL.format(branch_name)
    hit_request = requests.get(hit_url, headers=HEADERS)
    return hit_request.json()["download_url"]


def get_github_rate_limit_status():
    hit_request = requests.get(os.environ["GITHUB_RATELIMIT_ENDPOINT"], headers=HEADERS)
    hit_response = hit_request.json()
    hit_response = hit_response["rate"]
    hit_response["reset_secs"] = hit_response["reset"] - time.time()
    hit_response["reset_mins"] = int((hit_response["reset"] - time.time()) / 60)
    return hit_response


def get_http_data(url):
    response = requests.get(urlparse(url).geturl(), headers=HEADERS)
    yml_data = yaml.load(response.text, Loader=yaml.SafeLoader)
    return yml_data


def get_particular_advisory(data):
    """
    Function to get the advisories from a particular z-stream release
    :data: The data of a particular version
    """
    try:
        advisories = data['assembly']['group']['advisories']
        if -1 in advisories.values() or 1 in advisories.values():
            return None
    except Exception:
        return None

    return advisories


def get_brew_event_id(data):
    """
    Function to get the brew_event id from the releases.yml file
    :data: The yml for a particular z-stream release
    """
    try:
        brew_event_id = data['assembly']['basis']['brew_event']
        return brew_event_id
    except KeyError:
        return None


def process_version_advisories(version, yml_data, seen):
    # This function processes advisories for a single version
    advisories = get_particular_advisory(yml_data[version])

    if advisories:
        jira_link = get_jira_link(yml_data[version])
        return advisories, jira_link
    else:
        return None, None


def get_advisories(branch_name):
    """
    Gets the list of advisories from the releases.yml file of an OpenShift release.
    Filters out releases with 'custom' assembly type.
    :param branch_name: OpenShift branch name in ocp-build-data. eg: openshift-4.10
    :returns: List of lists containing the advisories with the z-stream version. Eg:
                            [['4.11.6', {'extras': 102175, 'image': 102174, 'metadata': 102177, 'rpm': 102173}], ... ]
    """
    url = f"{os.environ['GITHUB_RAW_CONTENT_URL']}/{branch_name}/releases.yml"
    seen = {}
    MAX_DEPTH = 3
    yml_data = get_http_data(url).get('releases', None)

    if not yml_data:
        return None

    advisory_data = []
    for version in yml_data:
        if version in seen:
            continue

        assembly_data = yml_data[version].get('assembly', {})
        assembly_type = assembly_data.get('type', '').lower()

        # Skip 'custom' assembly types
        if assembly_type == 'custom':
            continue

        depth = 0
        current_version = version
        current_advisories, jira_link = process_version_advisories(current_version, yml_data, seen)
        if not current_advisories:
            current_advisories = {}

        while depth < MAX_DEPTH:
            depth += 1
            basis_version = yml_data[current_version].get('assembly', {}).get('basis', {}).get('assembly')
            if not basis_version or basis_version in seen:
                break

            basis_advisories, _ = process_version_advisories(basis_version, yml_data, seen)
            if basis_advisories:
                current_advisories.update(basis_advisories)
            current_version = basis_version

        # Apply override advisories specified with 'advisories!'
        override_advisories = yml_data[version].get('assembly', {}).get('group', {}).get('advisories!', {})
        if override_advisories:
            current_advisories.update(override_advisories)

        if current_advisories:
            advisory_data.append([version, current_advisories, jira_link])
        seen[version] = True

    return advisory_data


def get_jira_link(data):
    try:
        jira_link = data['assembly']['group']['release_jira']
        logger.debug(f"JIRA: {jira_link}")
        return jira_link
    except KeyError:
        logger.error("Could not find jira link")
        return None


def get_branch_advisory_ids(branch_name):
    advisory_data = {}
    if branch_name.split('-')[-1] in ["3.11", "4.5"]:  # versions which do not have releases.yml
        url = f"{os.environ['GITHUB_RAW_CONTENT_URL']}/{branch_name}/group.yml"
        yml_data = get_http_data(url)['advisories']
        advisory_data = {"current": yml_data, "previous": {}}
    else:
        advisories = get_advisories(branch_name)
        if advisories:
            for advisory in advisories:
                try:
                    jira_link = advisory[2]
                except IndexError:
                    jira_link = None  # Assign a default value
                advisory_data[advisory[0]] = [advisory[1], jira_link]
        if not advisories:  # If advisories is None or empty
            return {"current": {}, "previous": {}}  # Return empty data structure

    return advisory_data
