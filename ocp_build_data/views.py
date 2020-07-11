from rest_framework import generics
import lib.http_requests as http_req
from rest_framework.response import Response
from . import request_dispatcher


class GitStatsView(generics.ListAPIView):

    def get(self, request, *args, **kwargs):
        return Response(data=http_req.get_github_rate_limit_status())


class BranchData(generics.ListAPIView):

    def get(self, request, *args, **kwargs):
        request_type = request.query_params.get("type", None)

        if request_type is None:
            return Response(data={"status": "error", "message": "Missing \"type\" params in the url."})
        else:

            data = request_dispatcher.handle_get_request_for_branch_data_view(request)
            response = Response(data=data)
            return response
