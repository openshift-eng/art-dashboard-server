from rest_framework import generics
import lib.http_requests as http_req
from rest_framework.response import Response


class BranchData(generics.ListAPIView):

    def get(self, request, *args, **kwargs):
        all_branches = http_req.get_branch_details_for_ocp_build_data()
        response = Response(data=all_branches)
        return response
