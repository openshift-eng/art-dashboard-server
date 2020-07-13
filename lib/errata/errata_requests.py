import os
import requests
import json
from requests_kerberos import HTTPKerberosAuth, REQUIRED
from .decorators import update_keytab


@update_keytab
def get_advisory_data(advisory_id):

    """
    This method returns advisory data for a given id.
    :param advisory_id: The id of the advisory to get data for.
    :return: Dict, advisory data.
    """

    errata_endpoint = os.environ["ERRATA_ADVISORY_ENDPOINT"]
    errata_endpoint = errata_endpoint.format(advisory_id)

    kerberos_auth = HTTPKerberosAuth(mutual_authentication=REQUIRED, sanitize_mutual_error_response=False)

    response = requests.get(errata_endpoint, auth=kerberos_auth, verify=False)

    try:
        advisory_data = json.loads(response.text)
        response = format_advisory_data(advisory_data)
        return response
    except Exception as e:
        return None


def format_advisory_data(advisory_data):

    """
    This method filters the data for an advisory from errata to pick required content.
    :param advisory_data: The advisory data received from errata.
    :return: Dictionary of filtered response.
    """

    advisory_details = []
    bug_details = []
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

            advisory_details.append(advisory_detail)

    final_response["advisory_details"] = advisory_details

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

    final_response["bugs"] = bug_details

    return final_response
