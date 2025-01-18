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
from github import Github, GithubException
from jira import JIRA
import json
import re
import os
import jwt
import time
import uuid
import requests
from datetime import datetime, timedelta
from build_interface.settings import SECRET_KEY, SESSION_COOKIE_DOMAIN, JWTAuthentication


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
def test(request):
    return Response({
        "status": "success",
        "payload": "Setup successful!"
    }, status=200)


@api_view(["GET"])
def git_jira_api(request):

    TEST_ART_JIRA = "TEST-ART-999"

    file_content = request.query_params.get('file_content', None)
    image_name = request.query_params.get('image_name', None)
    release_for_image = request.query_params.get('release_for_image', None)
    jira_summary = request.query_params.get('jira_summary', None)
    jira_description = request.query_params.get('jira_description', None)
    jira_project_id = request.query_params.get('jira_project_id', None)
    jira_story_type_id = request.query_params.get('jira_story_type_id', None)
    jira_component = request.query_params.get('jira_component', None)
    jira_priority = request.query_params.get('jira_priority', None)
    image_type = request.query_params.get('image_type', None)
    payload_name = request.query_params.get('payload_name', None)

    git_test_mode_value = request.query_params.get('git_test_mode', None)
    jira_test_mode_value = request.query_params.get('jira_test_mode', None)

    # extract the host from the request.
    host = request.get_host()

    if image_type == 'other':
        # This is not needed when the image type is not for payload so make
        # payload something other than None so it can be treated as supplied.
        payload_name = 'Not needed'

    if not all([file_content, release_for_image, image_name, jira_summary, jira_description, jira_project_id, jira_story_type_id, jira_component, jira_priority, image_type, payload_name]):
        # These are all required. If any are missing, return an error and
        # list what the user passed in.
        return Response({
            "status": "failure",
            "error": "Missing required parameters",
            "parameters": {
                "file_content": file_content,
                "image_name": image_name,
                "release_for_image": release_for_image,
                "jira_summary": jira_summary,
                "jira_description": jira_description,
                "jira_project_id": jira_project_id,
                "jira_story_type_id": jira_story_type_id,
                "jira_component": jira_component,
                "jira_priority": jira_priority,
                "image_type": image_type,
                "payload_name": payload_name,
            }
        }, status=400)

    # Test mode is the default (e.g., when not specified) to force being intentional
    # about actually creating the PR and Jira.
    git_test_mode = False
    jira_test_mode = False
    if not git_test_mode_value or 'true' in git_test_mode_value.lower():
        git_test_mode = True
    if not jira_test_mode_value or 'true' in jira_test_mode_value.lower():
        jira_test_mode = True

    git_user = os.getenv("GIT_USER")
    if not git_user:
        return Response({
            "status": "failure",
            "error": "git user not in GIT_USER environment variable"
        }, status=500)

    if git_test_mode:
        # Just create a success status and fake PR without using the git API
        pr_status = {
            "status": "success",
            "payload": f"{host}: Fake PR created successfully",
            "pr_url": f"https://github.com/{git_user}/ocp-build-data/pull/10"
        }
    else:
        try:
            # Load the git token from an environment variable, later we can update the deployment
            # to get the token from a Kubernetes environment variable sourced from a secret.
            github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
            if not github_token:
                return Response({
                    "status": "failure",
                    "error": "git token not in GITHUB_PERSONAL_ACCESS_TOKEN environment variable"
                }, status=500)

            git_object = Github(github_token)

            def make_github_request(func, *args, **kwargs):
                """
                This function applies retry logic (with exponential backoff) to git api calls.
                It will raise exceptions for maximum number of retries exceeded, server error,
                and unexpected errors. GithubException 404 is propagated to the caller.
                """

                max_retries = 3
                retry_delay = 5
                last_message = ""
                func_error_str = f"Error on git API request to '{func.__name__}'"

                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except GithubException as e:
                        if e.status == 403 and "rate limit" in e.data.get("message", "").lower():
                            last_message = "Rate limit exceeded"
                        elif e.status == 404:
                            raise
                        elif 500 <= e.status < 600:
                            last_message = f"Server error {e.status}"
                        else:
                            last_message = f"Unknown error {e.status}, {e.data.get('message', '')}"
                        print(last_message + ", retrying in {retry_delay} seconds...")

                    except Exception as e:
                        print(f"Unexpected error: {func_error_str} {str(e)}")
                        raise Exception(f"{func_error_str}: {str(e)}")

                    time.sleep(retry_delay)
                    retry_delay *= 2

                raise Exception(f"Max retries exceeded, {func_error_str}; message: '{last_message}'")

            # Get the repository
            repo = make_github_request(git_object.get_repo, f"{git_user}/ocp-build-data")

            # Get the base branch where we will make the PR against.
            base_branch = make_github_request(repo.get_branch, release_for_image)

            # Generate a unique branch name based on current time so you can easily tell how
            # old the branch is in case we need to clean up.
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
            new_branch_name = f"art-dashboard-new-image-{timestamp}"

            # Create a new branch off the base branch
            make_github_request(repo.create_git_ref, ref=f"refs/heads/{new_branch_name}", sha=base_branch.commit.sha)

            # Create the file (images/pf-status-relay.yml) on the new branch
            file_path = f"images/{image_name}.yml"
            make_github_request(
                repo.create_file,
                path=file_path,
                message=f"{image_name} image add",
                content=file_content,
                branch=new_branch_name
            )

            # Create a pull request from the new branch to the base branch.
            # Since we don't yet have a Jira ID, we'll use Jira-TBD for now.
            pr = make_github_request(
                repo.create_pull,
                title=f"[JIRA-TBD] {image_name} image add",
                body=f"Ticket: JIRA-TBD\n\nThis PR adds the {image_name} image file",
                head=new_branch_name,
                base=release_for_image
            )

            print(f"Pull request created: {pr.html_url} on branch {new_branch_name}")
            pr_status = {
                "status": "success",
                "payload": "PR created successfully",
                "pr_url": pr.html_url
            }

        except GithubException as e:
            print(f"GithubException: {str(e)}")
            return Response({
                "status": "failure",
                "error": f"GithubException: {str(e)}"
            }, status=e.status)

        except Exception as e:
            print(f"Other Exception: {str(e)}")
            return Response({
                "status": "failure",
                "error": f"Other Exception: {str(e)}"
            }, status=500)

    # Extract the PR url from the pr_status
    pr_url = pr_status['pr_url']

    if jira_test_mode:
        jira_status = {
            "status": "success",
            "jira_url": f"https://issues.redhat.com/browse/{TEST_ART_JIRA}",
            "pr_url": pr_url
        }
        return Response(jira_status, status=200)
    else:
        # Login to Jira
        jira_email = os.environ.get('JIRA_EMAIL')
        jira_api_token = os.environ.get('JIRA_TOKEN')

        if not jira_email or not jira_api_token:
            return Response({
                "status": "failure",
                "error": "Missing Jira credentials: JIRA_EMAIL or JIRA_TOKEN values are missing"
            }, status=400)

        try:
            # Attempt to connect to Jira
            headers = JIRA.DEFAULT_OPTIONS["headers"].copy()
            headers["Authorization"] = f"Bearer {jira_api_token}"

            jira = JIRA(server='https://issues.redhat.com/', options={"headers": headers})

            # Test the connection by retrieving something basic (the user's profile).
            user = jira.current_user()
            if not user:
                return Response({
                    "status": "failure",
                    "error": "Failed to properly authenticate to Jira."
                }, status=400)

        except Exception as e:
            # Handle failed authentication or connection issues
            print(f"Authentication error: {str(e)}")
            return Response({
                "status": "failure",
                "error": f"Authentication error: {str(e)}"
            }, status=400)

        jira_data = {
            "project": {"key": jira_project_id},
            "summary": jira_summary,
            "description": jira_description,
            "issuetype": {"name": jira_story_type_id},
            "components": [{"name": jira_component}],
            "priority": {"name": jira_priority},
        }

        try:
            # Attempt to create the Jira
            new_jira = jira.create_issue(fields=jira_data)

            jiraID = new_jira.key

            def add_subtask(jira_key: str, subtask_data: dict, assignee: str) -> None:
                subtask_data = {
                    "project": {"key": "ART"},
                    "issuetype": {"name": "Sub-task"},
                    "parent": {"key": jira_key},
                    "summary": subtask_data["summary"],
                    "description": subtask_data["description"],
                }
                if assignee:
                    subtask_data["assignee"] = {"name": assignee}
                try:
                    _ = jira.create_issue(fields=subtask_data)
                except Exception as e:
                    print(f"Error creating subtask on {jira_key}: {str(e)}; subtask_data: {subtask_data}")

            # For all images, add these subtasks:
            jira_subtask_data = {
                "summary": "pre-flight: Is under branching management",
                "description": "Confirm that the repository has release branches set up"
            }
            add_subtask(jiraID, jira_subtask_data, "")

            jira_subtask_data = {
                "summary": "pre-flight: Has openshift-priv set up",
                "description": "Confirm that the repo exists in openshift-priv"
            }
            add_subtask(jiraID, jira_subtask_data, "")

            jira_subtask_data = {
                "summary": "pre-merge: Add the image as a component in openshift/org repo",
                "description": "This is a new image and. As such, add it as a Backstage component in https://gitlab.cee.redhat.com/openshift/org"
            }
            add_subtask(jiraID, jira_subtask_data, "")

            jira_subtask_data = {
                "summary": "pre-merge: Is in ocp-build-data:main/product.yml",
                "description": "Confirm that the repo exists in ocp-build-data:main/product.yml"
            }
            add_subtask(jiraID, jira_subtask_data, "")

            # For payload images, add this subtasks:
            if image_type == "cvo-payload":
                jira_subtask_data = {
                    "summary": "pre-flight: Has staff engineer approval",
                    "description": f"Staff Engineer has approved for image {image_name} to be included in the payload as {payload_name} starting with version {release_for_image}."
                }
                add_subtask(jiraID, jira_subtask_data, "jdelft")

            # For new OLM managed operators, add these subtasks:
            if image_type == "olm-managed":
                jira_subtask_data = {
                    "summary": "pre-flight: Has PM approval",
                    "description": f"Confirm that there is PM approval to add {image_name} to {release_for_image}"
                }
                add_subtask(jiraID, jira_subtask_data, "")

        except Exception as e:
            return Response({
                "status": "failure",
                "error": f"An error occurred while creating the jira: {str(e)}; jira_data: {jira_data}"
            }, status=400)

        try:
            # Now that we have a Jira, attempt to patch the PR title with the JiraID
            pr.edit(title=f"[{jiraID}] {image_name} image add")
            pr.edit(body=f"Ticket: {jiraID}\n\nThis PR adds the {image_name} image file")
        except Exception as e:
            return Response({
                "status": "failure",
                "error": f"An error occurred while patching the PR: {str(e)}"
            }, status=400)

        jira_status = {
            "status": "success",
            "jira_url": f"https://issues.redhat.com/browse/{jiraID}",
            "pr_url": pr_url
        }
        return Response(jira_status, status=200)


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
