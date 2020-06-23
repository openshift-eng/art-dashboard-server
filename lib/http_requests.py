"""
This module has helper functions to make http requests to other apis.
"""

import requests
import ocp_build_data.constants as app_constants
import lib.constants as constants
import traceback


def get_all_ocp_build_data_branches():

    """
    This function lists all the branches of the ocp-build-data repository.
    :return: dict, all the branches along with their details.
    """

    try:
        req = requests.get(app_constants.GITHUB_URL_TO_LIST_ALL_OCP_BUILD_DATA_BRANCHES)
        branches = req.json()

        for branch in branches:
            if "name" in branch:
                if constants.OCP_BUILD_DATA_RELEVANT_BRANCHES_REGEX_COMPILER.match(branch["name"]):
                    branch_data = dict()
                    branch_data["name"] = branch["name"]
                    version = branch["name"].split("openshift-")[1]
                    branch_data["version"] = float(version)
                    branch_data["priority"] = 0
                    yield branch_data

    except Exception as e:
        traceback.print_exc()


def get_branch_details_for_ocp_build_data():

    branches = get_all_ocp_build_data_branches()
    return_data = []

    for branch in branches:
        branch_group_yml_url = get_group_yml_file_url(branch["name"])
        branch["group_yml_url"] = branch_group_yml_url
        return_data.append(branch)

    return return_data


def get_group_yml_file_url(branch_name: str) -> dict:

    """
    This method takes a branch name of ocp_build_data as a parameter and returns advisories details for the same.
    :param branch_name: Branch name of ocp_build_data
    :return: adivsories details
    """

    hit_url = app_constants.GITHUB_GROUP_YML_CONTENTS_URL.format(branch_name)
    hit_request = requests.get(hit_url)
    return hit_request.json()["download_url"]
