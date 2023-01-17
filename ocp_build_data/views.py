from rest_framework import generics
import lib.http_requests as http_req
from rest_framework.response import Response


class GitStatsView(generics.ListAPIView):

    def get(self, request, *args, **kwargs):
        return Response(data=http_req.get_github_rate_limit_status())
