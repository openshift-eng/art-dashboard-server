from django.urls import re_path
from .views import AutoComplete

urlpatterns = [
    re_path('', AutoComplete.as_view(), name='auto_complete_base'),
]
