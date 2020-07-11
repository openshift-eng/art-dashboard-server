from django.conf.urls import url
from .views import BranchData, GitStatsView

urlpatterns = [
    url('branch/', BranchData.as_view(), name='branch_data_view'),
    url('gitstats/', GitStatsView.as_view(), name='git_stats'),
]
