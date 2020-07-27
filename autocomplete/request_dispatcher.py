from .models import AutoCompleteRecord


def handle_autocomplete_get_request(request):

    request_type = request.query_params.get("type", None)

    if not request_type:
        return {
            "status": "error",
            "message": "Missing query param \"type\".",
            "data": []
        }
    elif request_type == "dg_name":
        records = AutoCompleteRecord.objects.filter(type=request_type).values_list('value', flat=True)
        return {
            "status": "success",
            "message": "Here is your data.",
            "data": records
        }
    else:
        return {
            "status": "error",
            "message": "Invalid request type.",
            "data": []
        }


def handle_autocomplete_post_request(request):

    request_type = request.query_params.get("type", None)

    if not request_type:
        return {
            "status": "error",
            "message": "Missing query param \"type\".",
            "data": []
        }
    elif request_type == "dg_name":
        status = AutoCompleteRecord.objects.insert_new_missing_records_for_type("dg_name")
        if status == 0:
            return {
                "status": "success",
                "message": "Autocomplete records updated successfully.",
                "data": []
            }
        else:
            return {
                "status": "error",
                "message": "Something went wrong.",
                "data": []
            }
    else:
        return {
            "status": "error",
            "message": "Invalid request type.",
            "data": []
        }
