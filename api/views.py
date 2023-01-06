from build.models import Build
from rest_framework import viewsets
from .serializer import BuildSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.image_pipeline import pipeline_image_names
from api.util import get_ga_version
import json
import re


class BuildViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A read-only view set (https://www.django-rest-framework.org/api-guide/viewsets/#readonlymodelviewset) to get
    build data from ART mariadb database.
    Results are paginated: https://github.com/ashwindasr/art-dashboard-server/tree/master/api#get-apiv1builds
    """
    queryset = Build.objects.all()
    serializer_class = BuildSerializer
    filter_backends = [DjangoFilterBackend]  # add feature to filter by URL request eg: /v1/builds/?page=2
    filterset_fields = "__all__"  # so that all columns can be filtered using URL


@api_view(["GET"])
def pipeline_from_github_api_endpoint(request):
    """
    Endpoint to get the image pipeline starting from GitHub, distgit, brew, cdn or delivery
    :param request: The GET request from the client
    :returns: JSON response containing all data. Eg:
                                {
                                    "status": str,
                                    "payload": {
                                        "openshift_version": str,
                                        "github_repo": str,
                                        "upstream_github_url": str,
                                        "private_github_url": str,
                                        "distgit": [
                                            {
                                                "distgit_repo_name": str,
                                                "distgit_url": "str,
                                                "brew": {
                                                    "brew_id": int,
                                                    "brew_build_url": str,
                                                    "brew_package_name": str,
                                                    "bundle_component": str,
                                                    "bundle_distgit": str,
                                                    "payload_tag": str,
                                                    "cdn": [
                                                        {
                                                            "cdn_repo_id": int,
                                                            "cdn_repo_name": str,
                                                            "cdn_repo_url": str,
                                                            "variant_name": str,
                                                            "variant_id": int,
                                                            "delivery": {
                                                                "delivery_repo_id": str,
                                                                "delivery_repo_name": str,
                                                                "delivery_repo_url": str}}]}}]}}

    """
    starting_from = request.query_params.get("starting_from", None)
    name = request.query_params.get("name", None)
    version = request.query_params.get("version", None)

    # validate input
    if re.match(r"^[a-z]+$", starting_from) and re.match(r"^[a-z0-9/\-]+$", name) and re.match(r"^\d+.\d+$", version):
        try:
            if not version:
                version = get_ga_version()  # Default version set to GA version, if unspecified

            if starting_from.lower().strip() == "github":
                result, status_code = pipeline_image_names.pipeline_from_github(name, version)
            elif starting_from.lower().strip() == "distgit":
                result, status_code = pipeline_image_names.pipeline_from_distgit(name, version)
            elif starting_from.lower().strip() == "brew":
                result, status_code = pipeline_image_names.pipeline_from_brew(name, version)
            elif starting_from.lower().strip() == "cdn":
                result, status_code = pipeline_image_names.pipeline_from_cdn(name, version)
            elif starting_from.lower().strip() == "delivery":
                result, status_code = pipeline_image_names.pipeline_from_delivery(name, version)
            else:
                result, status_code = {
                                          "status": "error",
                                          "payload": "Invalid value in field 'starting_from'"
                                      }, 400
        except Exception:
            result, status_code = {
                                      "status": "error",
                                      "payload": "Error while retrieving GA version"
                                  }, 500
    else:
        result, status_code = {
                                  "status": "error",
                                  "payload": "Invalid input values"
                              }, 400

    json_string = json.loads(json.dumps(result, default=lambda o: o.__dict__))

    return Response(json_string, status=status_code)


@api_view(["GET"])
def ga_version(request):
    try:
        result, status_code = {
                                  "status": "success",
                                  "payload": get_ga_version()
                              }, 200
    except Exception:
        result, status_code = {
                                  "status": "error",
                                  "payload": "Error while retrieving GA version"
                              }, 500

    json_string = json.loads(json.dumps(result, default=lambda o: o.__dict__))

    return Response(json_string, status=status_code)


@api_view(["GET"])
def test(request):
    return Response({
        "status": "success",
        "payload": "Setup successful!"
    }, status=200)
