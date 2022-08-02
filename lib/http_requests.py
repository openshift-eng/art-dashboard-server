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
from ocp_build_data.models import OpenShiftCurrentAdvisory


def get_all_ocp_build_data_branches():
    """
    This function lists all the branches of the ocp-build-data repository.
    :return: dict, all the branches along with their details.
    """

    try:
        req = requests.get(app_constants.GITHUB_URL_TO_LIST_ALL_OCP_BUILD_DATA_BRANCHES)
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
        except Exception as e:
            print("Something wrong with openshift versions on ocp-build-data branch names.")

        return branches_data

    except Exception as e:
        traceback.print_exc()
        return []


def get_branch_details_for_ocp_build_data(branch_name):
    branch_group_yml_url = get_group_yml_file_url(branch_name)
    return branch_group_yml_url


def get_group_yml_file_url(branch_name: str) -> dict:
    """
    This method takes a branch name of ocp_build_data as a parameter and returns advisories details for the same.
    :param branch_name: Branch name of ocp_build_data
    :return: adivsories details
    """
    hit_url = app_constants.GITHUB_GROUP_YML_CONTENTS_URL.format(branch_name)
    hit_request = requests.get(hit_url)
    return hit_request.json()["download_url"]


def get_github_rate_limit_status():
    hit_request = requests.get(os.environ["GITHUB_RATELIMIT_ENDPOINT"])
    hit_response = hit_request.json()
    hit_response = hit_response["rate"]
    hit_response["reset_secs"] = hit_response["reset"] - time.time()
    hit_response["reset_mins"] = int((hit_response["reset"] - time.time()) / 60)
    return hit_response


def get_advisory_ids_from_sha(sha):
    group_yml_url = os.environ["GITHUB_RAW_CONTENT_URL"].format(sha)
    hit_request = requests.get(group_yml_url)
    hit_response = yaml.load(hit_request.text)
    if "advisories" in hit_response:
        return hit_response["advisories"]
    return {}


def get_advisories(branch_name):
    yml_file = f"https://raw.githubusercontent.com/openshift/ocp-build-data/{branch_name}/releases.yml"
    response = requests.get(yml_file)
    yml_data = yaml.load(response.text, Loader=yaml.Loader)['releases']

    advisory_data = []
    for version in yml_data:
        try:
            advisories = yml_data[version]['assembly']['group']['advisories']
            brew_event = yml_data[version]['assembly']['basis']['brew_event']
        except:
            continue
        # advisory_data += list(advisories)
        if -1 in advisories or 1 in advisories:
            continue
        advisory_data.append([brew_event, advisories])

    return sorted(advisory_data, key=lambda x: x[0], reverse=True)


def get_branch_advisory_ids(branch_name):
    hit_response = get_advisories(branch_name)

    if hit_response:
        if not OpenShiftCurrentAdvisory.objects.check_if_current_advisories_match(branch_name=branch_name,
                                                                                  advisories=hit_response):
            OpenShiftCurrentAdvisory.objects.delete_old_entries_and_create_new(branch_name=branch_name,
                                                                               advisories=hit_response)

    return {"current": hit_response[0][1], "previous": hit_response[1][1]}


def get_commits_for_groupyml(branch_name):
    url = os.environ["GITHUB_ALL_COMMITS_GROUPYML"].format(branch_name)
    hit_request = requests.get(url)

    commits = hit_request.json()
    return commits
