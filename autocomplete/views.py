from rest_framework.response import Response
from rest_framework import generics
from autocomplete.request_dispatcher import handle_autocomplete_get_request, handle_autocomplete_post_request

# Create your views here.


class AutoComplete(generics.ListAPIView, generics.CreateAPIView):

    def create(self, request, *args, **kwargs):
        data = handle_autocomplete_post_request(request)
        return Response(data=data)

    def get(self, request, *args, **kwargs):
        data = handle_autocomplete_get_request(request)
        return Response(data=data)
