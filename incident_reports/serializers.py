from rest_framework import serializers
from datetime import datetime
from .models import Incident


class IncidentSerializer(serializers.Serializer):

    title = serializers.CharField(required=True, max_length=100)
    description = serializers.CharField(max_length=20000, required=True)
    impact = serializers.CharField(max_length=20000, required=False, allow_null=True, allow_blank=True)
    cause = serializers.CharField(max_length=20000, required=False, allow_null=True, allow_blank=True)
    remedy = serializers.CharField(max_length=20000, required=False, allow_null=True, allow_blank=True)
    action_items = serializers.CharField(max_length=20000, required=False, allow_null=True, allow_blank=True)
    incident_start = serializers.DateTimeField(required=False, default=datetime.now)
    incident_end = serializers.DateTimeField(required=False, allow_null=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        return_status = Incident.objects.create_new_incident(validated_data)

        if not return_status:
            return {
                "status": 0,
                "message": "ok",
                "data": [validated_data]
            }
        else:
            return {
                "status": 1,
                "message": "error",
                "data": []
            }

    def get_error_response(self):

        return {
            "status": 1,
            "message": self.errors,
            "data": []
        }


class IncidentUpdateSerializer(IncidentSerializer):

    log_incident_id = serializers.IntegerField(required=True)
    title = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    description = serializers.CharField(max_length=20000, required=False, allow_null=True, allow_blank=True)
    impact = serializers.CharField(max_length=20000, required=False, allow_null=True, allow_blank=True)
    cause = serializers.CharField(max_length=20000, required=False, allow_null=True, allow_blank=True)
    remedy = serializers.CharField(max_length=20000, required=False, allow_null=True, allow_blank=True)
    action_items = serializers.CharField(max_length=20000, required=False, allow_null=True, allow_blank=True)
    incident_start = serializers.DateTimeField(required=False, allow_null=True)
    incident_end = serializers.DateTimeField(required=False, allow_null=True)

    def update_incident(self):
        try:
            valid_data = self.validated_data
            Incident.objects.update_record_by_id(valid_data)
            return {
                "status": 0,
                "message": "ok",
                "data": self.validated_data
            }
        except Exception as e:
            print(e)
            return {
                "status": 1,
                "message": "error",
                "data": []
            }


class IncidentDeleteSerializer(serializers.Serializer):

    log_incident_id = serializers.IntegerField(required=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    @staticmethod
    def get_error_response():

        return {
            "status": 1,
            "message": "Something went wrong with deletion.",
            "data": []
        }

    def delete(self):
        return Incident.objects.delete_incident(self.validated_data["log_incident_id"])
