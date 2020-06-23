from django.conf.urls import url
from .views import BranchData

urlpatterns = [
    url('data/', BranchData.as_view(), name='branch_data_view')
]
