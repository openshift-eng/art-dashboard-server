"""
This module has helper functions to make http requests to other apis.
"""

import requests
import ocp_build_data.constants as app_constants
import lib.constants as constants
import traceback
import os
import yaml
import time

HEADERS = {"Authorization": f"token {os.environ['GITHUB_PERSONAL_ACCESS_TOKEN']}"}


def get_all_ocp_build_data_branches():
    """
    This function lists all the branches of the ocp-build-data repository.
    :return: dict, all the branches along with their details.
    """

    try:
        req = requests.get(app_constants.GITHUB_URL_TO_LIST_ALL_OCP_BUILD_DATA_BRANCHES, headers=HEADERS)
        branches = req.json()
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
    response = requests.get(url, headers=HEADERS)
    yml_data = yaml.load(response.text, Loader=yaml.Loader)
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


def get_advisories(branch_name):
    """
    Gets the list of advisories from the releases.yml file of an openshift release.
    :param branch_name: Openshift branch name in ocp-build-data. eg: openshift-4.10
    :returns: List of lists containing the advisories with the z-stream version. Eg:
                            [['4.11.6', {'extras': 102175, 'image': 102174, 'metadata': 102177, 'rpm': 102173}], ... ]
    """
    url = f"{os.environ['GITHUB_RAW_CONTENT_URL']}/{branch_name}/releases.yml"
    seen = {}  # variable to keep track of already processed openshift versions.
    yml_data = get_http_data(url).get('releases', None)

    if not yml_data:
        return None

    advisory_data = []
    for version in yml_data:
        if version in seen:
            continue  # If we have already included the advisories of a version

        try:
            _ = yml_data[version]['assembly']['basis']
        except KeyError:
            continue  # To make sure assembly and basis keys are present. Eg art3171 in 4.7 does not have those.

        brew_event_id = get_brew_event_id(yml_data[version])

        has_advisories = False  # flag to check if a child that inherits has advisories, in case that has precedence
        recursion_depth = 0  # counter to prevent infinite loops
        while not brew_event_id:
            recursion_depth += 1
            if recursion_depth == 1000:  # Set maximum recursion depth
                break

            advisories = get_particular_advisory(yml_data[version])
            if advisories:
                advisory_data.append([version, advisories])
                has_advisories = True
                break  # exit if advisories exist even though child inherits
            else:
                version = yml_data[version]['assembly']['basis']['assembly']  # get the parent version number
                brew_event_id = get_brew_event_id(yml_data[version])  # update the brew_event id

        if version not in seen:
            seen[version] = 1  # add version to seen as we have processed the advisories

        if has_advisories:
            continue  # continue if inherited child has advisories, which is already processed in the while loop

        advisories = get_particular_advisory(yml_data[version])
        if advisories:
            advisory_data.append([version, advisories])

    return advisory_data


def get_branch_advisory_ids(branch_name):
    if branch_name.split('-')[-1] in ["3.11", "4.5"]:  # versions which do not have releases.yml
        url = f"{os.environ['GITHUB_RAW_CONTENT_URL']}/{branch_name}/group.yml"
        yml_data = get_http_data(url)['advisories']

        return {"current": yml_data, "previous": {}}

    advisories = get_advisories(branch_name)

    if advisories:
        return {"current": advisories[0][-1], "previous": advisories[1][-1]}
    return {"current": {}, "previous": {}}
