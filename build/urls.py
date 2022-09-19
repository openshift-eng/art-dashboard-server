from django.urls import re_path
from .views import BuildView, DailyBuildReportView, DailyBuildFilterView

urlpatterns = [
    re_path(r'^$', BuildView.as_view(), name='build_view'),
    re_path('daily/', DailyBuildReportView.as_view(), name='daily_build_requests'),
    re_path('build_records/', DailyBuildFilterView.as_view(), name="daily_build_filter_view"),
]
