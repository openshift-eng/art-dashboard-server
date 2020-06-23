from django.db import models
import datetime
from django.core import serializers
from django.utils.timezone import now
import json

# Create your models here.


def generate_auto_health_request_with_missing_start_time(request_type):

    start_time, end_time = None, None

    if request_type == "hourly":
        start_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:00:00")
        end_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00")

    elif request_type == "daily":
        start_time = datetime.datetime.utcnow().strftime("%Y-%m-%d 00:00:00")
        end_time = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")

    return start_time, end_time


class HealthRequestManager(models.Manager):

    def create_new_request(self, request_type, start, end, status):
        new_request = self.create(type=request_type, start_time=start, end_time=end, status=status)

        if not new_request.save():
            return "success", new_request.request_id
        else:
            return "error", None

    def handle_build_health_request(self, request):

        start_time = end_time = None

        request_type = request["type"]

        if "start" in request:
            start_time = request["start"]

        if "end" in request:
            end_time = request["end"]

        if not start_time:
            start_time, end_time = generate_auto_health_request_with_missing_start_time(request_type=request_type)

        any_old_request = self.filter(type=request_type, start_time=start_time, end_time=end_time, status=False).first()

        if any_old_request:
            any_old_request = json.loads(serializers.serialize('json', [any_old_request, ]))
            return "Restarting an old request.", "success", any_old_request[0]["pk"]
        else:
            status, request_id = self.create_new_request(request_type=request_type, start=start_time, end=end_time, status=False)
            return "New build request generated.", status, request_id

    def is_request_already_satisfied(self, request):

        start_time = end_time = None

        request_type = request["type"]

        if "start" in request:
            start_time = request["start"]

        if "end" in request:
            end_time = request["end"]

        if not start_time:
            start_time, end_time = generate_auto_health_request_with_missing_start_time(request_type=request_type)

        previous_request = self.filter(type=request_type, start_time=start_time, end_time=end_time).first()
        if previous_request:
            previous_request = json.loads(serializers.serialize('json', [previous_request, ]))
            previous_request = previous_request[0]
            return previous_request["fields"]["status"]
        else:
            previous_request = False
        return previous_request

    def get_all_requests_for_a_type(self, request_type):

        requests = self.filter(type=request_type).all()
        if requests:
            requests = json.loads(serializers.serialize('json', [request for request in requests]))
        else:
            requests = []
        return requests


class HealthRequests(models.Model):

    request_id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=20, blank=False, null=False, choices=(("d", "daily"), ("h", "hourly")))
    start_time = models.DateTimeField(null=False, blank=False)
    end_time = models.DateTimeField(null=False, blank=False)
    status = models.BooleanField(null=False, blank=False, default=False)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(default=now)
    objects = HealthRequestManager()
