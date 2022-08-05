from build.models import Build
from rest_framework import viewsets
from .serializer import BuildSerializer
from django_filters.rest_framework import DjangoFilterBackend


class BuildViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Build.objects.all()
    serializer_class = BuildSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'
