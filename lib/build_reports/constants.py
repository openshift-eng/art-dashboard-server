GROUP_BY_COLUMNS = ["fault_code", "date_format(iso_time,\"%Y-%m-%d\")", "dg_name", "label_name", "label_version"]
BUILD_TABLE_COLUMN = {
    "brew.build_ids": "build_id",
    "brew.faultCode": "fault_code",
    "brew.task_id": "task_id",
    "brew.task_state": "task_state",
    "build.time.iso": "iso_time",
    "build.time.unix": "unix_time",
    "dg.commit": "dg_commit",
    "dg.name": "dg_name",
    "dg.namespace": "dg_namespace",
    "group": "group",
    "jenkins.build_number": "jenkins_build_number",
    "jenkins.build_url": "jenkins_build_url",
    "jenkins.job_name": "jenkins_job_name",
    "jenkins.job_url": "jenkins_job_url",
    "label.name": "label_name",
    "label.version": "label_version"
}
