from rest_framework import routers
from . import views
from . import product_views
from django.urls import include, re_path

router = routers.SimpleRouter()
router.register(r'builds', views.BuildViewSet)

urlpatterns = [
    re_path(r'^products/$', product_views.products),
    re_path(r'^products/overview/$', product_views.overview),
    re_path(r'^products/(?P<product_id>[a-z0-9-]+)/groups/$', product_views.groups),
    re_path(r'^products/(?P<product_id>[a-z0-9-]+)/releases/$', product_views.releases),
    re_path(r'^products/(?P<product_id>[a-z0-9-]+)/release/$', product_views.release_detail),
    re_path(r'', include(router.urls)),
    re_path('pipeline-image', views.pipeline_from_github_api_endpoint),
    re_path('ga-version', views.ga_version),
    re_path('shipment/status/', views.shipment_status, name='shipment_status'),
    re_path('branch/', views.branch_data, name='branch_data_view'),
    re_path('test', views.test),
    re_path('git_jira_api', views.git_jira_api),
    re_path('rpms_images_fetcher', views.rpms_images_fetcher_view),
    re_path('login', views.login_view, name='login'),
    re_path('check_auth', views.check_auth, name='check_auth')
]
