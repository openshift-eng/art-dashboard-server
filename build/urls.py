from django.conf.urls import url
from .views import BuildView

urlpatterns = [
    url('', BuildView.as_view(), name='build_view')
]
