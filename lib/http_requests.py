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

    access_token = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]

    try:
        req = requests.get(app_constants.GITHUB_URL_TO_LIST_ALL_OCP_BUILD_DATA_BRANCHES,
                           headers={"Authorization": "token " + access_token})
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
    access_token = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
    hit_url = app_constants.GITHUB_GROUP_YML_CONTENTS_URL.format(branch_name)
    hit_request = requests.get(hit_url, headers={"Authorization": "token " + access_token})
    return hit_request.json()["download_url"]


def get_github_rate_limit_status():
    access_token = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
    hit_request = requests.get(os.environ["GITHUB_RATELIMIT_ENDPOINT"], headers={"Authorization": "token " + access_token})
    hit_response = hit_request.json()
    hit_response = hit_response["rate"]
    hit_response["reset_secs"] = hit_response["reset"] - time.time()
    hit_response["reset_mins"] = int((hit_response["reset"] - time.time())/60)
    return hit_response


def get_advisory_ids_from_sha(sha):
    group_yml_url = os.environ["GITHUB_RAW_CONTENT_URL"].format(sha)
    access_token = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
    hit_request = requests.get(group_yml_url,
                               headers={"Authorization": "token " + access_token})
    hit_response = yaml.load(hit_request.text)
    if "advisories" in hit_response:
        return hit_response["advisories"]
    return {}


def get_branch_advisory_ids(branch_name):
    group_yml_url = os.environ["GITHUB_RAW_CONTENT_URL"].format(branch_name)
    access_token = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
    hit_request = requests.get(group_yml_url,
                               headers={"Authorization": "token " + access_token})
    hit_response = yaml.load(hit_request.text)
    if "advisories" in hit_response:
        if OpenShiftCurrentAdvisory.objects.check_if_current_advisories_match(
                branch_name=branch_name,
                advisories=hit_response["advisories"]):
            pass
        else:
            handle_mismatch_of_current_advisory_ids(branch_name=branch_name, advisories=hit_response["advisories"])

    return OpenShiftCurrentAdvisory.objects.get_advisories_for_branch(branch_name)
    # return {}


def handle_mismatch_of_current_advisory_ids(branch_name, advisories):
    current_advisories = advisories
    commits = get_commits_for_groupyml(branch_name=branch_name)

    current_advisories, current_advisories_sha = \
        find_current_advisory(commits=commits, current_advisories=current_advisories)

    previous_advisories, previous_advisories_sha = \
        find_previous_advisory(commits=commits, current_advisories=current_advisories)

    OpenShiftCurrentAdvisory.objects.delete_old_entries_and_create_new(branch_name=branch_name,
                                                                       current_advisories=current_advisories,
                                                                       previous_advisories=previous_advisories,
                                                                       current_sha=current_advisories_sha,
                                                                       previous_sha=previous_advisories_sha)


def is_this_an_advisory_update_commit(commit):

    commit_message_have_words = ['group.yml', 'advisory', 'advisories', 'update', 'group', 'yml']
    commit_message = commit["commit"]["message"]
    commit_message = commit_message.split(" ")
    word_match_count = 0
    for word in commit_message:
        for commit_message_have_word in commit_message_have_words:
            if word.lower()  in commit_message_have_word:
                word_match_count += 1
                break

    if word_match_count >= 3:
        return True
    return False


def find_current_advisory(commits, current_advisories):

    for commit in commits:
        if is_this_an_advisory_update_commit(commit=commit):
            this_commit_advisories = get_advisory_ids_from_sha(commit["sha"])
            for key in this_commit_advisories:
                if key in current_advisories and current_advisories[key] == this_commit_advisories[key]:
                    continue
                else:
                    return this_commit_advisories, commit["sha"]
            else:
                return current_advisories, commit["sha"]
    return None


def find_previous_advisory(commits, current_advisories):

    found_first = False

    for commit in commits:
        if is_this_an_advisory_update_commit(commit=commit):
            this_commit_advisories = get_advisory_ids_from_sha(commit["sha"])
            if not found_first:
                for key in this_commit_advisories:
                    if key in current_advisories and current_advisories[key] == this_commit_advisories[key]:
                        continue
                    else:
                        break
                else:
                    found_first = True
            else:
                return this_commit_advisories, commit["sha"]
    return {}


def get_commits_for_groupyml(branch_name):
    url = os.environ["GITHUB_ALL_COMMITS_GROUPYML"].format(branch_name)
    access_token = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
    hit_request = requests.get(url,
                               headers={"Authorization": "token " + access_token})

    commits = hit_request.json()
    return commits
