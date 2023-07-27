from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.models import User
from rest_framework import filters, viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.fetchers import rpms_images_fetcher
from api.image_pipeline import pipeline_image_names
from api.util import get_ga_version
from build.models import Build
from . import request_dispatcher
from .serializer import BuildSerializer

import django_filters
import json
import re
import os


class BuildDataFilter(django_filters.FilterSet):
    class Meta:
        model = Build
        fields = {
            "build_0_id": ["icontains", "exact"],
            "dg_name": ["icontains", "exact"],
            "brew_task_state": ["exact"],
            "brew_task_id": ["icontains", "exact"],
            "group": ["icontains", "exact"],
            "dg_commit": ["icontains", "exact"],
            "label_io_openshift_build_commit_id": ["icontains", "exact"],
            "time_iso": ["exact"],
            "jenkins_build_url": ["icontains", "exact"],
        }


class BuildViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A read-only view set (https://www.django-rest-framework.org/api-guide/viewsets/#readonlymodelviewset) to get
    build data from ART mariadb database.
    Results are paginated: https://github.com/ashwindasr/art-dashboard-server/tree/master/api#get-apiv1builds
    """
    queryset = Build.objects.all()
    serializer_class = BuildSerializer
    filter_backends = [DjangoFilterBackend,
                       filters.OrderingFilter]  # add feature to filter by URL request eg: /v1/builds/?page=2
    # Explicitly specify which fields the API may be ordered against
    # ordering_fields = ()
    filterset_class = BuildDataFilter

    # This will be used as the default ordering
    ordering = ("-build_time_iso")


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
    if re.match(r"^[A-Za-z]+$", starting_from) and re.match(r"^[A-Za-z0-9/\-]+$", name) and re.match(r"^\d+.\d+$", version):
        try:
            if not version:
                version = get_ga_version()  # Default version set to GA version, if unspecified

            if starting_from.lower().strip() == "github":
                result, status_code = pipeline_image_names.pipeline_from_github(name, version)
            elif starting_from.lower().strip() == "distgit":
                result, status_code = pipeline_image_names.pipeline_from_distgit(name, version)
            elif starting_from.lower().strip() == "package":
                result, status_code = pipeline_image_names.pipeline_from_package(name, version)
            elif starting_from.lower().strip() == "cdn":
                result, status_code = pipeline_image_names.pipeline_from_cdn(name, version)
            elif starting_from.lower().strip() == "image":
                result, status_code = pipeline_image_names.pipeline_from_image(name, version)
            else:
                result, status_code = {
                    "status": "error",
                    "payload": "Invalid value in field 'starting_from'"
                }, 400
        except Exception:
            result, status_code = {
                "status": "error",
                "payload": "Error while retrieving the image pipeline"
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
def branch_data(request):
    request_type = request.query_params.get("type", None)

    if request_type is None:
        return Response(data={"status": "error", "message": "Missing \"type\" params in the url."})
    elif request_type in ["advisory", "all", "openshift_branch_advisory_ids"]:
        data = request_dispatcher.handle_get_request_for_branch_data_view(request)
        response = Response(data=data)
        return response


@api_view(["GET"])
def test(request):
    return Response({
        "status": "success",
        "payload": "Setup successful!"
    }, status=200)


@api_view(["GET"])
def rpms_images_fetcher_view(request):
    release = request.query_params.get("release", None)

    if release is None:
        return Response(data={"status": "error", "message": "Missing \"release\" params in the url."})

    # Always fetch data
    try:
        result = rpms_images_fetcher.fetch_data(release)
    except Exception as e:
        return Response({
            "status": "error",
            "payload": f"An error occurred while fetching data from GitHub: {e}"
        }, status=500)

    return Response({
        "status": "success",
        "payload": result
    }, status=200)


@api_view(["POST"])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    # Validate against environment variables
    if username == os.environ.get('ART_DASH_PRIVATE_USER') and password == os.environ.get('ART_DASH_PRIVATE_PASSWORD'):
        try:
            # Fetch the user or create a new one if it does not exist
            user, created = User.objects.get_or_create(username=username)
            if created:
                # If the user is created for the first time, set the password
                user.set_password(password)
                user.save()

        except Exception as e:
            return Response({'detail': f'Error during user creation or password setting: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Authenticate the user
        user = authenticate(request, username=username, password=password, backend='django.contrib.auth.backends.ModelBackend')

        if user is not None:
            login(request, user)
            return Response({'detail': 'Login successful'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def check_auth(request):
    if request.user.is_authenticated:
        return Response({'detail': 'Authenticated'}, status=status.HTTP_200_OK)
    else:
        return Response({'detail': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
