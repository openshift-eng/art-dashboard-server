from django.db import models, connection
import datetime as dt
from django.core import serializers
from django.utils.timezone import now
import json
from lib.build_reports.daily_import import import_daily_data

from datetime import datetime
from time import strftime

# Create your models here.


class UnixTimestampField(models.DateTimeField):
    """UnixTimestampField: creates a DateTimeField that is represented on the
    database as a TIMESTAMP field rather than the usual DATETIME field.
    """
    def __init__(self, null=False, blank=False, **kwargs):
        super(UnixTimestampField, self).__init__(**kwargs)
        # default for TIMESTAMP is NOT NULL unlike most fields, so we have to
        # cheat a little:
        self.blank, self.isnull = blank, null
        self.null = True # To prevent the framework from shoving in "not null".

    def db_type(self, connection):
        typ=['TIMESTAMP']
        # See above!
        if self.isnull:
            typ += ['NULL']
        if self.auto_created:
            typ += ['default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP']
        return ' '.join(typ)

    def to_python(self, value):
        if isinstance(value, int):
            return datetime.fromtimestamp(value)
        else:
            return models.DateTimeField.to_python(self, value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if value==None:
            return None
        # Use '%Y%m%d%H%M%S' for MySQL < 4.1
        return strftime('%Y-%m-%d %H:%M:%S',value.timetuple())


def generate_auto_health_request_with_missing_start_time(request_type):

    start_time, end_time = None, None

    if request_type == "hourly":
        start_time = dt.datetime.utcnow().strftime("%Y-%m-%d %H:00:00")
        end_time = (dt.datetime.utcnow() + dt.timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00")

    elif request_type == "daily":
        start_time = dt.datetime.utcnow().strftime("%Y-%m-%d 00:00:00")
        end_time = (dt.datetime.utcnow()).strftime("%Y-%m-%d 00:00:00")

    return start_time, end_time


class BuildManager(models.Manager):

    def generate_build_data_for_ui(self, query_string):
        raw_results = self.raw(query_string)

        results = []

        for raw_result in raw_results:
            result = dict()
            result["build_id"] = raw_result.build_id
            result["fault_code"] = raw_result.fault_code
            result["task_id"] = raw_result.task_id
            result["iso_time"] = raw_result.iso_time
            result["group"] = raw_result.group
            result["label_name"] = raw_result.label_name
            result["jenkins_build_url"] = raw_result.jenkins_build_url
            result["nvr"] = raw_result.nvr
            result["build_source"] = raw_result.build_source
            result["dg_name"] = raw_result.dg_name
            result["build_commit_url_github"] = raw_result.build_commit_url_github
            result["jenkins_build_url"] = raw_result.jenkins_build_url
            result["jenkins_build_number"] = raw_result.jenkins_build_number
            result["jenkins_job_name"] = raw_result.jenkins_job_name
            result["build_name"] = raw_result.build_name
            result["build_version"] = raw_result.build_version
            results.append(result)

        return results

    def get_all_for_a_date_for_a_column(self, column_name, column_value, date):
        raw_results = self.raw(
            "select build_record_id, build_id, fault_code, task_id, iso_time, `group`, label_name jenkins_build_url from log_build where date(iso_time) = \"{}\" and {}=\"{}\"".format(
                date, column_name, column_value))
        results = []
        for raw_result in raw_results:
            result = dict()
            result["build_id"] = raw_result.build_id
            result["fault_code"] = raw_result.fault_code
            result["task_id"] = raw_result.task_id
            result["iso_time"] = raw_result.iso_time
            result["group"] = raw_result.group
            result["label_name"] = raw_result.label_name
            result["jenkins_build_url"] = raw_result.jenkins_build_url
            results.append(result)
        return results

    def get_all_for_a_date(self,date):

        raw_results = self.raw("select build_record_id, build_id, fault_code, task_id, iso_time, `group`, label_name jenkins_build_url from log_build where date(iso_time) = \"{}\"".format(date))
        results = []
        for raw_result in raw_results:
            result = dict()
            result["build_id"] = raw_result.build_id
            result["fault_code"] = raw_result.fault_code
            result["task_id"] = raw_result.task_id
            result["iso_time"] = raw_result.iso_time
            result["group"] = raw_result.group
            result["label_name"] = raw_result.label_name
            result["jenkins_build_url"] = raw_result.jenkins_build_url
            results.append(result)
        return results

    @staticmethod
    def generate_daily_report(date, request_id):

        cursor = connection.cursor()
        try:
            cursor.execute("insert into log_build_daily_summary(fault_code, date, dg_name, label_name, label_version, request_id, count) select fault_code, date_format(iso_time, \"%Y-%m-%d\") as date, dg_name,  label_name, label_version, {} as request_id,   count(*) as count from log_build where date_format(iso_time, \"%Y-%m-%d\") = \"{}\" group by 1,2,3,4,5".format(request_id, date))
            HealthRequests.objects.update_daily_report_status_for_a_date(request_id)
            return True
        except Exception as e:
            print(e)
            return False

    def write_to_db_import_data(self, date, data):

        for data_point in data:
            m = self.create(**data_point)

            if not m.save():
                pass
            else:
                print("Something went wrong.")

        HealthRequests.objects.update_daily_import_status_for_a_date(date=date)


class HealthRequestManager(models.Manager):

    def update_daily_report_status_for_a_date(self, request_id):
        daily_request = \
            self.get(request_id=request_id)
        daily_request.status = True
        daily_request.save()

    def update_daily_import_status_for_a_date(self, date):
        daily_request = \
            self.get(start_time=date + " 00:00:00", end_time=date + " 00:00:00", type="daily_import")
        daily_request.status = True
        daily_request.save()

    def if_daily_import_request_already_satisfied(self, date):

        daily_request = \
            self.filter(start_time=date + " 00:00:00", end_time=date + " 00:00:00", type="daily_import").first()

        if daily_request:
            daily_request = json.loads(serializers.serialize('json', [daily_request, ]))
            # this is the place to initiate the import request
            if not daily_request[0]["fields"]["status"]:
                data = import_daily_data(date=date, request_id=daily_request[0]["pk"])
                Build.objects.write_to_db_import_data(date=date, data=data)
            return "success", daily_request[0]["pk"]
        else:
            new_request = self.create(type="daily_import", start_time=date + " 00:00:00", end_time=date + " 00:00:00", status=False)

            if not new_request.save():
                # this is the place to initiate the import request
                data = import_daily_data(date=date, request_id=new_request.request_id)
                Build.objects.write_to_db_import_data(data=data, date=date)
                return "success", new_request.request_id
            else:
                return "error", None

    def create_new_request(self, request_type, start, end, status):
        new_request = self.create(type=request_type, start_time=start, end_time=end, status=status)

        if not new_request.save():
            # this is the place to put a new request for a build
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
            # this is the place to start put a new request to some sort of queue
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

    """
    This class holds all the requests for the import, daily, hourly reports.
    """

    request_id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=20, blank=False, null=False, choices=(("d", "daily"), ("h", "hourly")))
    start_time = models.DateTimeField(null=False, blank=False)
    end_time = models.DateTimeField(null=False, blank=False)
    status = models.BooleanField(null=False, blank=False, default=False)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(default=now)
    objects = HealthRequestManager()


class Build(models.Model):

    """
    This class represents the build record table which holds all the
    build records that are dumped in SimpleDB. Let SimpleDB be there.
    """

    class Meta:
        db_table = "log_build"

    build_record_id = models.AutoField(primary_key=True)
    build_id = models.BigIntegerField(blank=True, null=True)
    request_id = models.BigIntegerField(blank=True, null=True)
    fault_code = models.CharField(blank=False, null=False, max_length=300)
    task_id = models.BigIntegerField(blank=True, null=True)
    task_state = models.CharField(max_length=20, null=True, blank=True)
    iso_time = models.DateTimeField()
    unix_time = models.FloatField()
    dg_commit = models.CharField(max_length=300)
    dg_name = models.CharField(max_length=300)
    dg_namespace = models.CharField(max_length=300)
    group = models.CharField(max_length=300)
    jenkins_build_number = models.BigIntegerField()
    jenkins_build_url = models.URLField()
    jenkins_job_name = models.CharField(max_length=300)
    jenkins_job_url = models.URLField()
    label_name = models.CharField(max_length=300)
    label_version = models.CharField(max_length=300)
    nvr = models.CharField(max_length=1000, default=None, null=True)
    build_source = models.CharField(max_length=1000, default=None, null=True)
    build_commit_url_github = models.CharField(max_length=1000, default=None, null=True)
    build_version = models.CharField(max_length=100, default=None, null=True)
    build_name = models.CharField(max_length=1000, default=None, null=True)
    created_at = UnixTimestampField(auto_created=True, null=True)
    updated_at = UnixTimestampField(auto_created=True, null=True)
    objects = BuildManager()


class DailyBuildReportManager(models.Manager):

    def handle_request_for_daily_report_view_get(self, request_type, date=None):

        if request_type == "overview":
            daily_stats = self.raw("select 1 as log_build_daily_summary_id, date,sum( if(fault_code = 0, count,0)) as success, sum( if(fault_code != 0, count, 0)) as failure, sum(count) as total, (sum( if(fault_code = 0, count,0))/sum(count))*100 as success_rate  from log_build_daily_summary group by 2 order by 2 desc")
            daily_stats_filters = []
            for daily_stat in daily_stats:
                d_stat = {"date": daily_stat.date,
                          "success": daily_stat.success,
                          "failure": daily_stat.failure,
                          "total": daily_stat.total,
                          "success_rate": daily_stat.success_rate}

                daily_stats_filters.append(d_stat)

            return daily_stats_filters

        elif request_type == "fordate":
            if date is None:
                return []
            else:
                date_wise_stats = self.raw("select 1 as log_build_daily_summary_id, date, label_name, sum( if(fault_code = 0, count,0)) as success, sum( if(fault_code != 0, count, 0)) as failure, sum(count) as total, (sum( if(fault_code = 0,count,0))/sum(count))*100 as success_rate  from log_build_daily_summary where date=\"{0}\" group by 2,3 order by 7,6 desc".format(date))
                date_wise_stats_filtered = []
                total = success = failure = 0
                for date_wise_stat in date_wise_stats:
                    d_stat = {"date": date_wise_stat.date,
                              "success": date_wise_stat.success,
                              "failure": date_wise_stat.failure,
                              "total": date_wise_stat.total,
                              "success_rate": date_wise_stat.success_rate,
                              "label_name": date_wise_stat.label_name}

                    total += date_wise_stat.total
                    success += date_wise_stat.success
                    failure += date_wise_stat.failure

                    date_wise_stats_filtered.append(d_stat)

                data = {
                    "total": total,
                    "success": success,
                    "failure": failure,
                    "success_rate": (success/total)*100,
                    "table_data": date_wise_stats_filtered
                }
                return data
        elif request_type == "datewise_fault_code_stats":
            if date is None:
                return []
            else:
                fault_code_wise_stats = self.raw("select 1 as log_build_daily_summary_id, case when fault_code = \"\" then \"unknown\" else fault_code end as fault_code,sum(count) as count from log_build_daily_summary where date=\"{0}\" group by 2".format(date))
                fault_code_wise_stats_filtered = []
                for fault_code_wise_stat in fault_code_wise_stats:
                    d_stat = {"fault_code": fault_code_wise_stat.fault_code,
                              "count": fault_code_wise_stat.count}
                    fault_code_wise_stats_filtered.append(d_stat)

                return fault_code_wise_stats_filtered
        else:
            return {"message": "Invalid request type."}


class DailyBuildReport(models.Model):

    class Meta:
        db_table = "log_build_daily_summary"

    log_build_daily_summary_id = models.AutoField(primary_key=True)
    fault_code = models.CharField(max_length=300)
    date = models.DateField()
    dg_name = models.CharField(max_length=300)
    label_name = models.CharField(max_length=300)
    label_version = models.CharField(max_length=300)
    count = models.BigIntegerField()
    request_id = models.BigIntegerField(null=True, blank=True)
    created_at = UnixTimestampField(auto_created=True)
    updated_at = UnixTimestampField(auto_created=True)
    objects = DailyBuildReportManager()
