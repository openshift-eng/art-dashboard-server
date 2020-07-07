from django.conf.urls import url
from .views import BuildHealthRequestView, ImportBuildDataRequest, DailyBuildReportView, DailyBuildFilterView

urlpatterns = [
    url('request/', BuildHealthRequestView.as_view(), name='build_health_requests'),
    url('import/', ImportBuildDataRequest.as_view(), name='build_import_requests'),
    url('daily/', DailyBuildReportView.as_view(), name='daily_build_requests'),
    url('build_records', DailyBuildFilterView.as_view(), name="daily_build_filter_view"),
]
