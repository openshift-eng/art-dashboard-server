import os
import requests
import json
from requests_kerberos import HTTPKerberosAuth, OPTIONAL
from .decorators import update_keytab


@update_keytab
def get_advisory_data(advisory_id):
    """
    This method returns advisory data for a given id.
    :param advisory_id: The id of the advisory to get data for.
    :return: Dict, advisory data.
    """

    try:
        errata_endpoint = os.environ["ERRATA_ADVISORY_ENDPOINT"]
        errata_endpoint = errata_endpoint.format(advisory_id)

        kerberos_auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)

        response = requests.get(errata_endpoint, auth=kerberos_auth)
        advisory_data = json.loads(response.text)
        response = format_advisory_data(advisory_data)
        return response
    except Exception as e:
        print(e)
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
        errata_endpoint = errata_endpoint.format(user_id)

        kerberos_auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)

        response = requests.get(errata_endpoint, auth=kerberos_auth)
        user_data = json.loads(response.text)
        response = format_user_data(user_data)
        return response
    except Exception as e:
        print(e)
        return None


def format_user_data(user_data):
    return user_data


def format_advisory_data(advisory_data):
    """
    This method filters the data for an advisory from errata to pick required content.
    :param advisory_data: The advisory data received from errata.
    :return: Dictionary of filtered response.
    """

    advisory_details = []
    bug_details = []
    bug_summary = dict()
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

    if "bugs" in advisory_data:
        bug_data = advisory_data["bugs"]

        if "bugs" in bug_data:
            bug_data = bug_data["bugs"]

            for each_bug in bug_data:
                each_bug = each_bug["bug"]
                bug = dict()
                bug["id"] = each_bug["id"]
                bug["bug_status"] = each_bug["bug_status"]
                bug["bug_link"] = "https://bugzilla.redhat.com/show_bug.cgi?id=" + str(each_bug["id"])
                bug_details.append(bug)

                if bug["bug_status"] not in bug_summary:
                    bug_summary[bug["bug_status"]] = 0

                bug_summary[bug["bug_status"]] += 1
                total_bugs += 1

    final_response["bugs"] = bug_details
    bug_summary_array = []
    for key in bug_summary:
        bug_summary_array.append({"bug_status": key,
                                  "count": bug_summary[key],
                                  "percent": round((bug_summary[key] / total_bugs) * 100, 2)})

    final_response["bug_summary"] = bug_summary_array

    return final_response
