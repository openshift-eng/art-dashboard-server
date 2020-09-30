from rest_framework import serializers
from datetime import datetime
from .models import Incident


class IncidentSerializer(serializers.Serializer):

    description = serializers.CharField(max_length=20000, required=True)
    impact = serializers.CharField(max_length=20000, required=False)
    cause = serializers.CharField(max_length=20000, required=False)
    remedy = serializers.CharField(max_length=20000, required=False)
    action_items = serializers.CharField(max_length=20000, required=False)
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
    description = serializers.CharField(max_length=20000, required=False)
    impact = serializers.CharField(max_length=20000, required=False)
    cause = serializers.CharField(max_length=20000, required=False)
    remedy = serializers.CharField(max_length=20000, required=False)
    action_items = serializers.CharField(max_length=20000, required=False)
    incident_start = serializers.DateTimeField(required=False)
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
