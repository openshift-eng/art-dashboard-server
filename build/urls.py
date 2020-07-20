from django.conf.urls import url
from .views import BuildView, BuildView1

urlpatterns = [
    url(r'^$', BuildView.as_view(), name='build_view'),
    url(r'^new/$', BuildView1.as_view(), name='build_view1'),
]
