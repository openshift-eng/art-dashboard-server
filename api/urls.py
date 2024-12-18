from rest_framework import routers
from . import views
from django.urls import include, re_path

router = routers.SimpleRouter()
router.register(r'builds', views.BuildViewSet)

urlpatterns = [
    re_path(r'', include(router.urls)),
    re_path('pipeline-image', views.pipeline_from_github_api_endpoint),
    re_path('ga-version', views.ga_version),
    re_path('branch/', views.branch_data, name='branch_data_view'),
    re_path('test', views.test),
    re_path('git_jira_api', views.git_jira_api),
    re_path('rpms_images_fetcher', views.rpms_images_fetcher_view),
    re_path('login', views.login_view, name='login'),
    re_path('check_auth', views.check_auth, name='check_auth')
]
