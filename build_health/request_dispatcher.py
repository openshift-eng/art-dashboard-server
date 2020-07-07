from .models import Build


def daily_build_filter_view_get(request):

    request_type = request.query_params.get("type", None)
    date = request.query_params.get("date", None)

    if request_type == "all":
        return Build.objects.get_all_for_a_date(date)
    else:
        return {"error": "Invalid request."}
