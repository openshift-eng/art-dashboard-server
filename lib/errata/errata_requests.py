import os
import requests
import json
from requests_kerberos import HTTPKerberosAuth, OPTIONAL
from .decorators import update_keytab
from urllib.parse import urlparse
from requests_gssapi import HTTPSPNEGOAuth
import ssl


@update_keytab
def get_advisory_data(advisory_id):
    """
    This method returns advisory data for a given id.
    :param advisory_id: The id of the advisory to get data for.
    :return: Dict, advisory data.
    """

    try:
        errata_endpoint = os.environ["ERRATA_ADVISORY_ENDPOINT"]
        jira_issues_endpoint = f"{os.environ['ERRATA_SERVER']}/advisory/{advisory_id}/jira_issues.json"
        response = requests.get(urlparse(errata_endpoint.format(advisory_id)).geturl(), verify=ssl.get_default_verify_paths().openssl_cafile, auth=HTTPSPNEGOAuth())
        if response.status_code != 200:
            return None
        advisory_data = json.loads(response.text)
        jira_response = requests.get(
            urlparse(jira_issues_endpoint).geturl(),
            verify=ssl.get_default_verify_paths().openssl_cafile,
            auth=HTTPSPNEGOAuth()
        )
        jira_issues_data = json.loads(jira_response.text)

        return format_advisory_data(advisory_data, jira_issues_data)

    except Exception:
        return None


@update_keytab
def get_user_data(user_id):
    """
        This method returns user data for a given id.
        :param user_id: The id of the user to get data for.
        :return: Dict, user data.
        """

    try:
        errata_endpoint = os.environ["ERRATA_USER_ENDPOINT"]

        response = requests.get(urlparse(errata_endpoint.format(user_id)).geturl(), verify=ssl.get_default_verify_paths().openssl_cafile, auth=HTTPSPNEGOAuth())
        return format_user_data(json.loads(response.text))
    except Exception as e:
        print(e)
        return None


def format_user_data(user_data):
    return user_data


def format_advisory_data(advisory_data, jira_issues_data):
    """
    This method filters the data for an advisory from errata to pick required content.
    :param advisory_data: The advisory data received from errata.
    :return: Dictionary of filtered response.
    """

    advisory_details = []
    final_response = {}

    if "errata" in advisory_data:
        errata_data = advisory_data["errata"]
        for key in errata_data:

            advisory_detail = dict()
            advisory_detail["advisory_type"] = key

            if "id" in errata_data[key]:
                advisory_detail["id"] = errata_data[key]["id"]
            else:
                advisory_detail["id"] = None

            if "release_date" in errata_data[key]:
                if errata_data[key]["release_date"] is None:
                    advisory_detail["release_date"] = "Unassigned"
                else:
                    advisory_detail["release_date"] = errata_data[key]["release_date"]
            else:
                advisory_detail["release_date"] = "Unassigned"

            if "publish_date" in errata_data[key]:
                if errata_data[key]["publish_date"] is None:
                    advisory_detail["publish_date"] = "Unassigned"
                else:
                    advisory_detail["publish_date"] = errata_data[key]["publish_date"].split("T")[0]
            else:
                advisory_detail["publish_date"] = "Unassigned"

            if "synopsis" in errata_data[key]:
                advisory_detail["synopsis"] = errata_data[key]["synopsis"]
            else:
                advisory_detail["synopsis"] = "Not Described"

            if "qa_complete" in errata_data[key]:
                if errata_data[key]["qa_complete"] == 0:
                    advisory_detail["qa_complete"] = "Requested"
                elif errata_data[key]["qa_complete"] == 1:
                    advisory_detail["qa_complete"] = "Complete"
                else:
                    advisory_detail["qa_complete"] = "Not Requested"
            else:
                advisory_detail["qa_complete"] = "Unknown"

            if "status" in errata_data[key]:
                advisory_detail["status"] = errata_data[key]["status"]
            else:
                advisory_detail["status"] = "Unknown"

            if "doc_complete" in errata_data[key]:
                if errata_data[key]["doc_complete"] == 1:
                    advisory_detail["doc_complete"] = "Approved"
                elif errata_data[key]["doc_complete"] == 0:
                    advisory_detail["doc_complete"] = "Requested"
                else:
                    advisory_detail["doc_complete"] = "Not Requested"

            else:
                advisory_detail["doc_complete"] = "Unknown"

            if "security_approved" in errata_data[key]:
                if errata_data[key]["security_approved"] == 1:
                    advisory_detail["security_approved"] = "Approved"
                elif errata_data[key]["security_approved"] == 0:
                    advisory_detail["security_approved"] = "Requested"
                else:
                    advisory_detail["security_approved"] = "Not Requested"
            else:
                advisory_detail["security_approved"] = "Unknown"

            if "content" in advisory_data and "content" in advisory_data["content"]:
                qe_reviewer_id = None

                doc_reviewer_id = advisory_data["content"]["content"]["doc_reviewer_id"] \
                    if "doc_reviewer_id" in advisory_data["content"]["content"] \
                    else None

                product_security_reviewer_id = advisory_data["content"]["content"]["product_security_reviewer_id"] \
                    if "product_security_reviewer_id" in advisory_data["content"]["content"] \
                    else None

                advisory_detail["qe_reviewer_id"] = qe_reviewer_id

                if qe_reviewer_id is not None:
                    advisory_detail["qe_reviewer_details"] = get_user_data(qe_reviewer_id)
                else:
                    advisory_detail["qe_reviewer_details"] = None

                advisory_detail["doc_reviewer_id"] = doc_reviewer_id

                if doc_reviewer_id is not None:
                    advisory_detail["doc_reviewer_details"] = get_user_data(doc_reviewer_id)
                else:
                    advisory_detail["doc_reviewer_details"] = None

                advisory_detail["product_security_reviewer_id"] = product_security_reviewer_id

                if product_security_reviewer_id is not None:
                    advisory_detail["product_security_reviewer_details"] = get_user_data(product_security_reviewer_id)
                else:
                    advisory_detail["product_security_reviewer_details"] = None

            advisory_details.append(advisory_detail)

    final_response["advisory_details"] = advisory_details

    total_bugs = 0
    jira_bugs_details = []
    total_jira_bugs = 0
    jira_bug_summary = dict()
    bugzilla_bugs_details = []
    total_bugzilla_bugs = 0
    bugzilla_bug_summary = dict()

    if jira_issues_data:
        for jira_issue in jira_issues_data:
            jira_bug_detail = {
                "id_jira": jira_issue.get("id_jira"),
                "key": jira_issue.get("key"),
                "summary": jira_issue.get("summary"),
                "status": jira_issue.get("status"),
                "is_private": jira_issue.get("is_private"),
                "labels": jira_issue.get("labels"),
            }
            jira_bugs_details.append(jira_bug_detail)
            total_jira_bugs += 1

            if jira_bug_detail["status"] not in jira_bug_summary:
                jira_bug_summary[jira_bug_detail["status"]] = 0
            jira_bug_summary[jira_bug_detail["status"]] += 1

    if "bugs" in advisory_data:
        bugzilla_data = advisory_data["bugs"]

        if "bugs" in advisory_data:
            bugzilla_data = advisory_data["bugs"]

            bug_data = bugzilla_data["bugs"]

            for each_bug in bug_data:
                each_bug = each_bug["bug"]
                bug = dict()
                bug["id"] = each_bug["id"]
                bug["bug_status"] = each_bug["bug_status"]
                bug["bug_link"] = "https://bugzilla.redhat.com/show_bug.cgi?id=" + str(each_bug["id"])
                bugzilla_bugs_details.append(bug)

                if bug["bug_status"] not in bugzilla_bug_summary:
                    bugzilla_bug_summary[bug["bug_status"]] = 0

                bugzilla_bug_summary[bug["bug_status"]] += 1
                total_bugzilla_bugs += 1

    final_response["bugs"] = bugzilla_bugs_details
    bug_summary_array = []
    for key in jira_bug_summary:
        if total_jira_bugs == 0:
            bug_summary_array.append({
                "bug_status": key,
                "count": jira_bug_summary[key],
            })
        else:
            bug_summary_array.append({
                "bug_status": key,
                "count": jira_bug_summary[key],
            })

    for key in bugzilla_bug_summary:
        if total_bugs == 0:
            bug_summary_array.append({
                "bug_status": key,
                "count": bugzilla_bug_summary[key],
            })
        else:
            bug_summary_array.append({
                "bug_status": key,
                "count": bugzilla_bug_summary[key],
            })

    final_response["bug_summary"] = bug_summary_array

    return final_response
