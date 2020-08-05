from rest_framework import generics
from rest_framework.response import Response
from .models import HealthRequests, Build, DailyBuildReport
from.serializers import HealthRequestViewSerializer, ImportBuildViewSerializer, DailyReportViewSerializer
from .request_dispatcher import daily_build_filter_view_get


class ImportBuildDataRequest(generics.CreateAPIView):
    serializer_class = ImportBuildViewSerializer

    def post(self, request, *args, **kwargs):

        serializer = ImportBuildViewSerializer(data=request.data)
        if serializer.is_valid():
            status, message = HealthRequests.objects.if_daily_import_request_already_satisfied(serializer.data["date"])
            return Response({"status": status, "message": message})
        else:
            return Response({"status": "error", "message": serializer.errors})


class DailyBuildReportView(generics.CreateAPIView, generics.ListAPIView):

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

    def post(self, request, *args, **kwargs):

        serializer = DailyReportViewSerializer(data=request.data)
        if serializer.is_valid():
            request = serializer.data
            request["type"] = "daily"
            request_status = HealthRequests.objects.is_request_already_satisfied(request)

            if not request_status:
                message, status, request_id = HealthRequests.objects.handle_build_health_request(request)

                if Build.objects.generate_daily_report(serializer.data["start"], request_id):
                    return Response(data={"status": "success", "message": "Daily report generated."})
                else:
                    return Response(data={"status": "error", "message": "Something went wrong."})
            else:
                return Response(data={"status": "error", "message": "Request already completed."})
        else:
            return Response({"status": "error", "message": serializer.errors})


class BuildHealthRequestView(generics.ListAPIView, generics.CreateAPIView):

    serializer_class = HealthRequestViewSerializer

    def get(self, request, *args, **kwargs):

        request_type = request.query_params.get('request_type', None)
        if request_type is None:
            return Response(data={"status": "error", "message": "Missing parameter \"request_type\"."})
        else:
            return Response(data={"status": "success",
                                  "data": HealthRequests.objects.get_all_requests_for_a_type(request_type=request_type)})

    def post(self, request, *args, **kwargs):

        data = request.data
        serializer = HealthRequestViewSerializer(data=data)

        if serializer.is_valid():
            request_status = HealthRequests.objects.is_request_already_satisfied(data)
            if request_status:
                return Response(data={"status": "success", "message": "Build report request already completed."})
            else:
                message, status, request_id = HealthRequests.objects.handle_build_health_request(data)
                return Response(data={"status": status,
                                      "data": {"request_id": request_id},
                                      "message": message})
        else:
            return Response(data={"error": serializer.errors})


class DailyBuildFilterView(generics.ListAPIView):

    def get(self, request, *args, **kwargs):

        request_type = request.query_params.get("type", None)
        date = request.query_params.get("date", None)

        if request_type and date:
            return Response({"status": "success", "data": daily_build_filter_view_get(request)})
        else:
            return Response({"status": "fail", "message": "Missing url params,", "data": []})
