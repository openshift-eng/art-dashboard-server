from django.conf.urls import url
from .views.advisory import Advisory
from .views.user import User

urlpatterns = [
    url('advisory/', Advisory.as_view(), name='errata_advisory_view'),
    url('user/', User.as_view(), name='errata_user_view')
]
