from rest_framework import generics
from .serializer import BuildSerializer
from rest_framework.response import Response
from lib.aws.sdb import SimpleDBClientManagerPool
from django.http import HttpResponse
import json
from .request_dispatcher import handle_build_post_request

# Create your views here.


class BuildView(generics.CreateAPIView, generics.ListAPIView):

    serializer_class = BuildSerializer

    def get(self, request, *args, **kwargs):
        return HttpResponse("<h1>Hello</h1>")

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = serializer.data
            poolManager = SimpleDBClientManagerPool()
            client_manager = poolManager.acquire()
            select_response = client_manager.run_select(data)
            poolManager.release(client_manager)
            response = Response(data=select_response)
            return response
        else:
            response = Response(data={"body": ["missing fields", serializer.errors]})
            return response


class BuildView1(generics.CreateAPIView):

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
