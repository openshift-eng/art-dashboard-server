from rest_framework import generics
from .serializer import BuildSerializer
from rest_framework.response import Response
from lib.aws.sdb import SimpleDBClientManagerPool

# Create your views here.


class BuildView(generics.CreateAPIView):

    serializer_class = BuildSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = request.data
            poolManager = SimpleDBClientManagerPool()
            client_manager = poolManager.acquire()
            select_response = client_manager.run_select(data)
            poolManager.release(client_manager)
            response = Response(data=select_response)
            print(response.data)
            return response
        else:
            response = Response(data={"body": ["missing fields", serializer.errors]})
            print(response.data)
            return response
