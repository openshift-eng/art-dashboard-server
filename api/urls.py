from rest_framework import routers
from . import views
from django.conf.urls import url, include

router = routers.SimpleRouter()
router.register(r'builds', views.BuildViewSet)

urlpatterns = [
    url(r'', include(router.urls))
]
