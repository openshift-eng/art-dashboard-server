from rest_framework import generics
from rest_framework.response import Response
from .serializers import IncidentSerializer, IncidentUpdateSerializer
from .models import Incident


class IncidentView(generics.ListAPIView, generics.CreateAPIView, generics.UpdateAPIView):

    def get(self, request, *args, **kwargs):
        data = Incident.objects.get_all_incident()
        return Response(data={
            "status": 0,
            "message": "ok",
            "data": data
        })

    def post(self, request, *args, **kwargs):

        serializer = IncidentSerializer(data=request.data)

        if serializer.is_valid():
            response = serializer.create(serializer.validated_data)
        else:
            response = serializer.get_error_response()

        return Response(data=response)

    def patch(self, request, *args, **kwargs):

        serializer = IncidentUpdateSerializer(data=request.data)

        if serializer.is_valid():
            response = serializer.update_incident()
        else:
            response = serializer.get_error_response()

        return Response(data=response)
