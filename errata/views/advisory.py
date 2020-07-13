from rest_framework import generics
from errata.request_dispatchers.advisory import validate_advisory_get, route_advisory_get
from rest_framework.response import Response


class Advisory(generics.ListAPIView):

    def get(self, request, *args, **kwargs):

        validation_status, result = validate_advisory_get(request)

        if validation_status:
            response = route_advisory_get(result)
            return Response(data=response)
        else:
            return Response(data=result)
