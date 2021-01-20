from django.conf.urls import url
from .views import BuildView, DailyBuildReportView, DailyBuildFilterView

urlpatterns = [
    url(r'^$', BuildView.as_view(), name='build_view'),
    url('daily/', DailyBuildReportView.as_view(), name='daily_build_requests'),
    url('build_records/', DailyBuildFilterView.as_view(), name="daily_build_filter_view"),
]
