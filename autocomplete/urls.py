from django.conf.urls import url
from .views import AutoComplete

urlpatterns = [
    url('', AutoComplete.as_view(), name='auto_complete_base'),
]
