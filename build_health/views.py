from rest_framework import generics
from rest_framework.response import Response
from.serializers import HealthRequestViewSerializer
from .models import HealthRequests


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
