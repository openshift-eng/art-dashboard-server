from django.urls import re_path
from .views import BranchData, GitStatsView

urlpatterns = [
    re_path('branch/', BranchData.as_view(), name='branch_data_view'),
    re_path('gitstats/', GitStatsView.as_view(), name='git_stats'),
]
