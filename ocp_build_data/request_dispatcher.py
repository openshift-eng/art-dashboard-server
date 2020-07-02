import lib.http_requests as http_req


def handle_get_request_for_branch_data_view(request):

    request_type = request.query_params.get("type", None)

    if request_type == "all":
        return http_req.get_all_ocp_build_data_branches()
    elif request_type == "openshift_branch_advisory_ids":
        branch_name = request.query_params.get("branch", None)
        if branch_name:
            return http_req.get_branch_advisory_ids(branch_name)
        else:
            return []
    else:
        return []
