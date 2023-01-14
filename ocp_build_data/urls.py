from django.urls import re_path
from .views import GitStatsView

urlpatterns = [
    re_path('gitstats/', GitStatsView.as_view(), name='git_stats'),
]
