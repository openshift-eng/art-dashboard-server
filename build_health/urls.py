from django.conf.urls import url
from .views import BuildHealthRequestView

urlpatterns = [
    url('request/', BuildHealthRequestView.as_view(), name='build_health_requests')
]
