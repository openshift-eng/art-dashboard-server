from django.urls import re_path
from .views.advisory import Advisory
from .views.user import User

urlpatterns = [
    re_path('advisory/', Advisory.as_view(), name='errata_advisory_view'),
    re_path('user/', User.as_view(), name='errata_user_view')
]
