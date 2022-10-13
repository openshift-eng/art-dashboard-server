from build.models import Build
from rest_framework import viewsets
from .serializer import BuildSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.image_pipeline import pipeline_image_names
from api.pr_in import nightly as nighlty_main
from api.translate_names import translate_names
import json


class BuildViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A read-only view set (https://www.django-rest-framework.org/api-guide/viewsets/#readonlymodelviewset) to get
    build data from ART mariadb database.
    Results are paginated: https://github.com/ashwindasr/art-dashboard-server/tree/master/api#get-apiv1builds
    """
    queryset = Build.objects.all()
    serializer_class = BuildSerializer
    filter_backends = [DjangoFilterBackend]  # add feature to filter by URL request eg: /v1/builds/?page=2
    filterset_fields = '__all__'  # so that all columns can be filtered using URL


@api_view(['GET'])
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

    if starting_from == "github":
        result, status_code = pipeline_image_names.pipeline_from_github(name, version)
    elif starting_from == "distgit":
        result, status_code = pipeline_image_names.pipeline_from_distgit(name, version)
    elif starting_from == "brew":
        result, status_code = pipeline_image_names.pipeline_from_brew(name, version)
    elif starting_from == "cdn":
        result, status_code = pipeline_image_names.pipeline_from_cdn(name, version)
    elif starting_from == "delivery":
        result, status_code = pipeline_image_names.pipeline_from_delivery(name, version)
    else:
        result, status_code = {
                                  "status": "error",
                                  "payload": "Invalid value in field 'starting_from'"
                              }, 400

    jsonstr = json.loads(json.dumps(result, default=lambda o: o.__dict__))

    return Response(jsonstr, status=status_code)


@api_view(['GET'])
def pr_in_nightly(request):
    arch = request.query_params.get("arch", None)
    version = request.query_params.get("version", None)
    repo = request.query_params.get("repo", None)
    pr = request.query_params.get("pr", None)
    commit = request.query_params.get("commit", None)

    if arch and version and repo and (pr or commit):
        result, status_code = nighlty_main.pr_in_nightly(arch, version, repo, pr, commit)
    else:
        result, status_code = {
                                  "status": "error",
                                  "payload": "Invalid Input"
                              }, 400

    return Response(result, status=status_code)


@api_view(['GET'])
def translate_names_view(request):
    name_type = request.query_params.get("name_type", None)
    name = request.query_params.get("name", None)
    name_type2 = request.query_params.get("name_type2", None)
    major = request.query_params.get("major", None)
    minor = request.query_params.get("minor", None)

    if name_type and name and name_type2:
        result, status_code = translate_names.translate_names_main(name_type, name, name_type2, major, minor)
    else:
        result, status_code = {
                                  "status": "error",
                                  "payload": "Invalid Input"
                              }, 400

    return Response(result, status=status_code)


@api_view(['GET'])
def test(request):
    return Response({
        "status": "success",
        "payload": "Setup successful"
    }, status=200)
