from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets, status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from api.fetchers import rpms_images_fetcher
from api.image_pipeline import pipeline_image_names
from api.util import get_ga_version
from build.models import Build
from . import request_dispatcher
from .serializer import BuildSerializer
import django_filters
import requests
import base64
import yaml
import json
import re
import os
import jwt
from datetime import datetime, timedelta
from build_interface.settings import SECRET_KEY, SESSION_COOKIE_DOMAIN, JWTAuthentication
from django.http import JsonResponse
from lib.errata.errata_requests import get_advisory_status_activities, get_advisory_schedule, get_feature_freeze_schedule, get_ga_schedule


class BuildDataFilter(django_filters.FilterSet):
    stream_only = django_filters.BooleanFilter(method='filter_stream_only')

    def filter_stream_only(self, queryset, name, value):
        if value:
            return queryset.filter(build_0_nvr__endswith='.assembly.stream')
        return queryset

    class Meta:
        model = Build
        fields = {
            "build_0_id": ["icontains", "exact"],
            "build_0_nvr": ["icontains", "exact"],
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
def get_advisory_activities(request):
    request_id = request.query_params.get("advisory", None)

    if request_id is None:
        return JsonResponse({"status": "error", "message": "Missing \"advisory\" params in the url."})
    else:
        return JsonResponse(get_advisory_status_activities(request_id))


@api_view(["GET"])
def get_release_schedule(request):
    request_type = request.query_params.get("type", None)
    branch_version = request.query_params.get("branch_version", None)

    if request_type is None:
        return JsonResponse({"status": "error", "message": "Missing \"type\" params in the url."})
    if request_type not in ["ga", "release", "feature_freeze"]:
        return JsonResponse({"status": "error", "message": "Invalid \"type\" params in the url. It sould be in ga,release,feature_freeze"})
    if branch_version is None:
        return JsonResponse({"status": "error", "message": "Missing \"branch_version\" params in the url."})
    if request_type == "ga":
        return JsonResponse(get_ga_schedule(branch_version), safe=False)
    elif request_type == "release":
        return JsonResponse(get_advisory_schedule(branch_version), safe=False)
    elif request_type == "feature_freeze":
        return JsonResponse(get_feature_freeze_schedule(branch_version), safe=False)


shipped_advisory = []

@api_view(["GET"])
def get_release_status(request):
    ga_version = get_ga_version()
    major, minor = int(ga_version.split('.')[0]), int(ga_version.split('.')[1])
    status = {"message":[], "alert":[], "unshipped": []}
    headers = {"Authorization": f"token {os.environ['GITHUB_PERSONAL_ACCESS_TOKEN']}"}
    for r in range(0, 4):
        version = minor - r
        advisory_schedule = get_advisory_schedule(f"{major}.{version}")['all_ga_tasks']
        for release in advisory_schedule:
            if datetime.strptime(release['date_finish'],"%Y-%m-%d") < datetime.now():
                release_date, release_name = release['date_finish'], release['name']
            else:
                break
        if "GA" in release_name:
            assembly = re.search(r'\d+\.\d+', release_name).group()+".0"
        else:
            assembly = re.search(r'\d+\.\d+.\d+', release_name).group()
        status['message'].append({"release":f"{major}.{version}", "status": f"{assembly} release date is {release_date} and {release['name']} release date is {release['date_finish']}"})
        res = requests.get(f"https://api.github.com/repos/openshift/ocp-build-data/contents/releases.yml?ref=openshift-{major}.{version}", headers=headers)
        release_assembly = yaml.safe_load(base64.b64decode(res.json()['content']))['releases'][assembly]['assembly']
        if "group" in release_assembly.keys():
            if 'advisories!' in release_assembly['group'].keys():
                advisories = release_assembly['group']['advisories!']
            elif 'advisories' in release_assembly['group'].keys():
                advisories = release_assembly['group']['advisories']
            else:
                advisories = {}
            for ad in advisories:
                if datetime.strptime(release_date,"%Y-%m-%d").strftime("%Y-%m-%d") == datetime.now().strftime("%Y-%m-%d"):
                    if advisories[ad] in shipped_advisory:
                        status['alert'].append({"release":f"{major}.{version}", "status": f"{assembly} <https://errata.devel.redhat.com/advisory/{advisories[ad]}|{ad}> advisory is shipped live"})
                    else:
                        errata_activity = get_advisory_status_activities(advisories[ad])['data']
                        if len(errata_activity) > 0:
                            errata_state = errata_activity[-1]['attributes']['added']
                        else:
                            errata_state = "NEW_FILES"
                        if errata_state == "SHIPPED_LIVE":
                            shipped_advisory.append(advisories[ad])
                            status['alert'].append({"release":f"{major}.{version}", "status": f"{assembly} <https://errata.devel.redhat.com/advisory/{advisories[ad]}|{ad}> advisory is shipped live"})
                        elif errata_state == "DROPPED_NO_SHIP":
                            status['alert'].append({"release":f"{major}.{version}", "status": f"{assembly} <https://errata.devel.redhat.com/advisory/{advisories[ad]}|{ad}> advisory is dropped"})
                        else:
                            status['alert'].append({"release":f"{major}.{version}", "status": f"{assembly} <https://errata.devel.redhat.com/advisory/{advisories[ad]}|{ad}> advisory is {errata_state}, release date is today"})
                            status['unshipped'].append({"advisory": advisories[ad], "note": f"{assembly} {ad} advisory"})
    return JsonResponse(status)


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
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if username == os.environ.get('ART_DASH_PRIVATE_USER') and password == os.environ.get('ART_DASH_PRIVATE_PASSWORD'):
        # Create a JWT token
        expiration = datetime.utcnow() + timedelta(hours=1)  # Set token to expire in 1 hour
        token = jwt.encode({
            'username': username,
            'exp': expiration
        }, SECRET_KEY, algorithm="HS256")

        # Create a response
        return Response({'detail': 'Login successful', 'token': token}, status=status.HTTP_200_OK)

    return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def check_auth(request):
    return Response({'detail': 'Authenticated'}, status=status.HTTP_200_OK)
