"""
This module has helper functions to make http requests to other apis.
"""
import copy
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

#### assembly merger methods ####
# The following methods have been copied over from
# github.com/openshift-eng/art-tools/artcommon/artcommonlib/assembly.py
# to work with assemblies. Please refer before changing

def _check_recursion(releases_config: dict, assembly: str):
    found = []
    next_assembly = assembly
    while next_assembly:
        if next_assembly in found:
            raise ValueError(f'Infinite recursion in {assembly} detected; {next_assembly} detected twice in chain')
        found.append(next_assembly)
        target_assembly = releases_config.get('releases', {}).get(next_assembly, {}).get('assembly', {})
        next_assembly = target_assembly.get('basis', {}).get('assembly', None)


def _assembly_field(field_name: str, releases_config: dict, assembly: str) -> dict:
    """
    :param field_name: the field name
    :param releases_config: The content of releases.yml in Model form.
    :param assembly: The name of the assembly to assess
    Returns the computed field for a given assembly.
    """
    _check_recursion(releases_config, assembly)
    target_assembly = releases_config.get('releases', {}).get(assembly, {}).get("assembly", {})
    current_assembly_field = target_assembly.get(field_name, {})
    basis_assembly = target_assembly.get("basis", {}).get("assembly", None)
    if basis_assembly:  # Does this assembly inherit from another?
        # Recursive apply ancestor assemblies
        basis_assembly_field = _assembly_field(field_name, releases_config, basis_assembly)
        current_assembly_field = _merger(current_assembly_field, basis_assembly_field)
    return current_assembly_field


def _merger(a, b):
    """
    Merges two, potentially deep, objects into a new one and returns the result.
    Conceptually, 'a' is layered over 'b' and is dominant when
    necessary. The output is 'c'.
    1. if 'a' specifies a primitive value, regardless of depth, 'c' will contain that value.
    2. if a key in 'a' specifies a list and 'b' has the same key/list, a's list will be appended to b's for c's list.
       Duplicates entries will be removed and primitive (str, int, ...) lists will be returned in sorted order.
    3. if a key ending with '!' in 'a' specifies a value, c's key (sans !) will be to set that value exactly.
    4. if a key ending with a '?' in 'a' specifies a value, c's key (sans ?)
       will be set to that value IF 'c' does not contain the key.
    4. if a key ending with a '-' in 'a' specifies a value, c's will not be populated
       with the key (sans -) regardless of 'a' or  'b's key value.
    """
    if type(a) in [bool, int, float, str, bytes, type(None)]:
        return a

    c = copy.deepcopy(b)

    if type(a) is list:
        if type(c) is not list:
            return a
        for entry in a:
            if entry not in c:  # do not include duplicates
                c.append(entry)

        if c and type(c[0]) in [str, int, float]:
            return sorted(c)
        return c

    if type(a) is dict:
        if type(c) is not dict:
            return a
        for k, v in a.items():
            if k.endswith('!'):  # full dominant key
                k = k[:-1]
                c[k] = v
            elif k.endswith('?'):  # default value key
                k = k[:-1]
                if k not in c:
                    c[k] = v
            elif k.endswith('-'):  # remove key entirely
                k = k[:-1]
                c.pop(k, None)
            else:
                if k in c:
                    c[k] = _merger(a[k], c[k])
                else:
                    c[k] = a[k]
        return c

    raise TypeError(f'Unexpected value type: {type(a)}: {a}')

#### assembly merger methods end ####

def get_advisories(branch_name):
    """
    Gets the list of advisories from the releases.yml file of an OpenShift release.
    Filters out releases with 'custom' assembly type or empty advisories.
    :param branch_name: OpenShift branch name in ocp-build-data. eg: openshift-4.10
    :returns: List of lists containing the advisories with the z-stream version. Eg:
                            [['4.11.6', {'extras': 102175, 'image': 102174, 'metadata': 102177, 'rpm': 102173}], ... ]
    """
    url = f"{os.environ['GITHUB_RAW_CONTENT_URL']}/{branch_name}/releases.yml"
    seen = {}
    MAX_DEPTH = 3
    yml_data = get_http_data(url)

    if not yml_data:
        return None

    advisory_data = []
    for version in yml_data.get("releases", {}):
        assembly_data = yml_data["releases"][version].get('assembly', {})
        assembly_type = assembly_data.get('type', '').lower()

        # Skip 'custom' assembly types
        if assembly_type == 'custom':
            continue
        group_data = _assembly_field("group", yml_data, version)
        advisories = group_data.get("advisories", {})
        jira_link = group_data.get("release_jira", "")
        advisory_data.append([version, advisories, jira_link])

    return advisory_data


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
