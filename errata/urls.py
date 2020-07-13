from django.conf.urls import url
from .views.advisory import Advisory

urlpatterns = [
    url('advisory/', Advisory.as_view(), name='advisory_view')
]
