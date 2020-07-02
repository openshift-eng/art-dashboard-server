from django.db import models
from build_health.models import DailyBuildReport, UnixTimestampField

# Create your models here.


class AutoCompleteRecordManager(models.Manager):

    def insert_new_missing_records_for_type(self, record_type):

        if record_type == "nvr":
            try:
                distinct_values = DailyBuildReport.objects.raw("select 1 as log_build_daily_summary_id, dg_name as nvr from log_build_daily_summary group by 2")
                all_values = set()
                for distinct_value in distinct_values:
                    all_values.add(distinct_value.nvr)

                self.raw("delete from log_autocomplete_record where type = {}".format(record_type))
                for value in all_values:
                    AutoCompleteRecord.objects.create(type=record_type, value=value).save()

                return 0
            except Exception as e:
                print(e)
                return 1
        else:
            return 1


class AutoCompleteRecord(models.Model):

    class Meta:
        db_table = "log_autocomplete_record"

    log_autocomplete_record_id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=50, blank=False, null=False)
    value = models.CharField(max_length=300, blank=False, null=False)
    created_at = UnixTimestampField(auto_created=True)
    updated_at = UnixTimestampField(auto_created=True)
    objects = AutoCompleteRecordManager()
