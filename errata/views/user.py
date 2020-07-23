from rest_framework import generics
from errata.request_dispatchers.user import validate_user_get, route_user_get
from rest_framework.response import Response


class User(generics.ListAPIView):

    def get(self, request, *args, **kwargs):

        validation_status, result = validate_user_get(request)

        if validation_status:
            response = route_user_get(result)
            return Response(data=response)
        else:
            return Response(data=result)
