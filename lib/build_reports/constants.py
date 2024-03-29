GROUP_BY_COLUMNS = ["fault_code", "date_format(iso_time,\"%Y-%m-%d\")", "dg_name", "label_name", "label_version"]

BUILD_TABLE_COLUMN = {
    "brew.build_ids": "build_id",
    "brew.faultCode": "fault_code",
    "brew.image_shas": "image_shas",
    "brew.task_id": "task_id",
    "brew.task_state": "task_state",
    "build.0.id": "build_0_id",
    "build.0.name": "build_0_name",
    "build.0.nvr": "build_0_nvr",
    "build.0.package_id": "build_0_package_id",
    "build.0.release": "build_0_release",
    "build.0.source": "build_0_source",
    "build.0.version": "build_0_version",
    "build.time.iso": "build_iso_time",
    "build.time.unix": "build_unix_time",
    "dg.commit": "dg_commit",
    "dg.name": "dg_name",
    "dg.namespace": "dg_namespace",
    "dg.qualified_key": "dg_qualified_key",
    "dg.qualified_name": "dg_qualified_name",
    "group": "group",
    "incomplete": "incomplete",
    "jenkins.build_number": "jenkins_build_number",
    "jenkins.build_url": "jenkins_build_url",
    "jenkins.job_name": "jenkins_job_name",
    "jenkins.job_url": "jenkins_job_url",
    "jenkins.node_name": "jenkins_node_name",
    "label.com.redhat.component": "label_com_redhat_component",
    "label.io.openshift.build.commit.id": "label_io_openshift_build_commit_id",
    "label.io.openshift.build.commit.url": "build_commit_url_github",
    "label.io.openshift.build.source-location": "label_io_openshift_build_source_location",
    "label.io.openshift.maintainer.product": "label_io_openshift_maintainer_product",
    "label.io.openshift.tags": "label_io_openshift_tags",
    "label.name": "label_name",
    "label.version": "label_version",
    "time.iso": "iso_time",
    "time.unix": "unix_time"
}
