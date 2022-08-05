from build.models import Build
from rest_framework import serializers


class BuildSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Build
        fields = '__all__'
