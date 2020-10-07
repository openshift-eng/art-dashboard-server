from django.conf.urls import url
from .views import IncidentView

urlpatterns = [
    url('', IncidentView.as_view(), name='incident_report_url'),
]
