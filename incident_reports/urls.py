from django.urls import re_path
from .views import IncidentView

urlpatterns = [
    re_path('', IncidentView.as_view(), name='incident_report_url'),
]
