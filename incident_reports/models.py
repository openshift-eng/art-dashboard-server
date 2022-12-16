from django.db import models
import datetime
from django.core import serializers
import json


# Create your models here.


class IncidentManager(models.Manager):

    @staticmethod
    def create_new_incident(incident):

        incident_model_instance = Incident(**incident)
        if not incident_model_instance.save():
            return 0
        return 1

    def update_record_by_id(self, incident):
        incident_instance = self.filter(log_incident_id=incident["log_incident_id"])

        if incident_instance:
            incident_instance.update(**incident)

    def get_all_incident(self):
        incidents = self.filter().order_by('-log_incident_id').all()
        return json.loads(serializers.serialize('json', [incident for incident in incidents]))

    def delete_incident(self, incident_id):
        try:
            self.filter(log_incident_id=incident_id).delete()
            return 0
        except Exception:
            return 1


class Incident(models.Model):
    class Meta:
        db_table = "log_incident"

    log_incident_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    impact = models.TextField(blank=True, null=True)
    cause = models.TextField(blank=True, null=True)
    remedy = models.TextField(blank=True, null=True)
    action_items = models.TextField(blank=True, null=True)
    incident_start = models.DateTimeField(default=datetime.datetime.now)
    incident_end = models.DateTimeField(default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    objects = IncidentManager()
