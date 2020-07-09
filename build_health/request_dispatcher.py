from .models import Build


def daily_build_filter_view_get(request):

    request_type = request.query_params.get("type", None)
    date = request.query_params.get("date", None)

    if request_type == "all":
        return Build.objects.get_all_for_a_date(date)
    elif request_type == "column_search":
        column_name = request.query_params.get("name", None)
        column_value = request.query_params.get("value", None)
        if column_name:
            return Build.objects.get_all_for_a_date_for_a_column(column_name, column_value, date)
    else:
        return {"error": "Invalid request."}
