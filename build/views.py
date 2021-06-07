from rest_framework import generics
from .serializer import BuildSerializer, DailyReportViewSerializer
from rest_framework.response import Response
import json
from .request_dispatcher import handle_build_post_request, daily_build_filter_view_get
from .models import DailyBuildReport


# Create your views here.


class BuildView(generics.CreateAPIView):

    def post(self, request, *args, **kwargs):

        post_data = dict()

        if isinstance(request.data, dict):
            post_data = request.data
        elif isinstance(request.data, str):

            if request.data == "":
                post_data = {}
            else:
                try:
                    post_data = json.loads(request.data)
                except ValueError as e:
                    return Response(
                        data={"status": "error", "message": "Invalid request format.", "data": [], "error": str(e)})
        response = handle_build_post_request(post_data)

        return Response(data=response)


class DailyBuildReportView(generics.CreateAPIView):

    serializer_class = DailyReportViewSerializer

    def get(self, request, *args, **kwargs):

        request_type = request.query_params.get("type", None)
        date = request.query_params.get("date", None)

        if request_type:
            return Response(
                data={"status": "success",
                      "data": DailyBuildReport.objects.handle_request_for_daily_report_view_get(request_type, date),
                      "message": "Data is ready."})
        else:
            return Response(data={"status": "error", "message": "Request type missing.", "data": None})


class DailyBuildFilterView(generics.ListAPIView):

    def get(self, request, *args, **kwargs):

        request_type = request.query_params.get("type", None)
        date = request.query_params.get("date", None)

        if request_type and date:
            return Response({"status": "success", "data": daily_build_filter_view_get(request)})
        else:
            return Response({"status": "fail", "message": "Missing url params,", "data": []})
