from django.db import models, connection
from datetime import datetime
from time import strftime
from .managers import BuildManager, DailyBuildReportManager


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
        self.null = True  # To prevent the framework from shoving in "not null".

    def db_type(self, connection):
        typ = ['TIMESTAMP']
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
        if value is None:
            return None
        # Use '%Y%m%d%H%M%S' for MySQL < 4.1
        return strftime('%Y-%m-%d %H:%M:%S', value.timetuple())


class DailyBuildReport(models.Model):
    class Meta:
        db_table = "log_build_daily_summary"
        managed = False

    log_build_daily_summary_id = models.AutoField(primary_key=True)
    fault_code = models.CharField(max_length=300, null=True, blank=True)
    date = models.DateField()
    dg_name = models.CharField(max_length=300, null=True, blank=True)
    label_name = models.CharField(max_length=300, null=True, blank=True)
    label_version = models.CharField(max_length=300, null=True, blank=True)
    count = models.BigIntegerField()
    request_id = models.BigIntegerField(null=True, blank=True)
    created_at = UnixTimestampField(auto_created=True)
    updated_at = UnixTimestampField(auto_created=True)
    objects = DailyBuildReportManager()


class Build(models.Model):
    """
    This class represents the build record table which holds all the
    build records that are dumped in SimpleDB. Let SimpleDB be there.
    """

    class Meta:
        db_table = "log_build"
        managed = False

    log_log_build_id = models.AutoField(primary_key=True)
    label_io_openshift_tags = models.CharField(max_length=1000, blank=True, null=True)
    dg_name = models.CharField(max_length=1000, blank=True, null=True)
    label_release = models.CharField(max_length=1000, blank=True, null=True)
    label_version = models.CharField(max_length=1000, blank=True, null=True)
    label_io_openshift_build_source_location = models.CharField(max_length=1000, blank=True, null=True)
    brew_task_state = models.CharField(max_length=1000, blank=True, null=True)
    label_com_redhat_component = models.CharField(max_length=1000, blank=True, null=True)
    dg_namespace = models.CharField(max_length=1000, blank=True, null=True)
    build_time_unix = models.BigIntegerField(blank=True, null=True)
    runtime_uuid = models.FloatField(blank=True, null=True)
    env_OS_GIT_TREE_STATE = models.CharField(max_length=1000, blank=True, null=True)
    dg_commit = models.CharField(max_length=1000, blank=True, null=True)
    env_OS_GIT_MINOR = models.BigIntegerField(blank=True, null=True)
    env_OS_GIT_MAJOR = models.BigIntegerField(blank=True, null=True)
    brew_task_id = models.BigIntegerField(blank=True, null=True)
    label_io_openshift_build_commit_id = models.CharField(max_length=1000, blank=True, null=True)
    env_OS_GIT_COMMIT = models.CharField(max_length=1000, blank=True, null=True)
    incomplete = models.CharField(max_length=1000, blank=True, null=True)
    env_OS_GIT_VERSION = models.CharField(max_length=1000, blank=True, null=True)
    group = models.CharField(max_length=1000, blank=True, null=True)
    dg_qualified_key = models.CharField(max_length=1000, blank=True, null=True)
    env_OS_GIT_PATCH = models.BigIntegerField(blank=True, null=True)
    time_iso = models.DateTimeField(blank=True, null=True)
    dg_qualified_name = models.CharField(max_length=1000, blank=True, null=True)
    label_io_openshift_build_commit_url = models.CharField(max_length=1000, blank=True, null=True)
    brew_faultCode = models.BigIntegerField(blank=True, null=True)
    build_time_iso = models.DateTimeField(blank=True, null=True)
    time_unix = models.BigIntegerField(blank=True, null=True)
    label_io_openshift_maintainer_product = models.CharField(max_length=1000, blank=True, null=True)
    label_name = models.CharField(max_length=1000, blank=True, null=True)
    label_io_openshift_maintainer_component = models.CharField(max_length=1000, blank=True, null=True)
    brew_build_ids = models.BigIntegerField(blank=True, null=True)
    jenkins_build_number = models.BigIntegerField(blank=True, null=True)
    build_0_package_id = models.BigIntegerField(blank=True, null=True)
    build_0_version = models.CharField(max_length=1000, blank=True, null=True)
    brew_image_shas = models.CharField(max_length=1000, blank=True, null=True)
    jenkins_job_name = models.CharField(max_length=1000, blank=True, null=True)
    runtime_user = models.CharField(max_length=1000, blank=True, null=True)
    jenkins_node_name = models.CharField(max_length=1000, blank=True, null=True)
    build_0_nvr = models.CharField(max_length=1000, blank=True, null=True)
    build_0_release = models.CharField(max_length=1000, blank=True, null=True)
    build_0_name = models.CharField(max_length=1000, blank=True, null=True)
    jenkins_job_url = models.CharField(max_length=1000, blank=True, null=True)
    build_0_id = models.BigIntegerField(blank=True, null=True)
    jenkins_build_url = models.CharField(max_length=1000, blank=True, null=True)
    build_0_source = models.CharField(max_length=1000, blank=True, null=True)
    label_io_openshift_maintainer_subcomponent = models.CharField(max_length=1000, blank=True, null=True)
    label_io_openshift_release_operator = models.CharField(max_length=1000, blank=True, null=True)
    label_io_openshift_expose_services = models.CharField(max_length=1000, blank=True, null=True)
    env_KUBE_GIT_MINOR = models.CharField(max_length=1000, blank=True, null=True)
    env_KUBE_GIT_VERSION = models.CharField(max_length=1000, blank=True, null=True)
    env_KUBE_GIT_MAJOR = models.BigIntegerField(blank=True, null=True)
    env_KUBE_GIT_COMMIT = models.CharField(max_length=1000, blank=True, null=True)
    env_KUBE_GIT_TREE_STATE = models.CharField(max_length=1000, blank=True, null=True)
    label_io_openshift_build_versions = models.CharField(max_length=1000, blank=True, null=True)
    label_io_openshift_s2i_scripts_url = models.CharField(max_length=1000, blank=True, null=True)
    created_at = UnixTimestampField(auto_created=True, null=True)
    updated_at = UnixTimestampField(auto_created=True, null=True)
    objects = BuildManager()
