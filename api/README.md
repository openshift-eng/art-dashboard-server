# ART-API

Base URL: ```http://art-dash-server-aos-art-web.apps.ocp4.prod.psi.redhat.com```

### GET /api/v1/builds
Prints all the build details. Results are paginated, per page 100 results. <br><br>
Eg:
```
{
    "count": 90322,
    "next": "http://localhost:8080/api/v1/builds/?page=2",
    "previous": null,
    "results": [
        {
            "url": "http://art-dash-server-aos-art-web.apps.ocp4.prod.psi.redhat.com/api/v1/builds/1/",
            "env_OS_GIT_MAJOR": 4,
            "build_0_package_id": null,
            "time_unix": 1629484778550,
            "runtime_user": "ocp-build",
            "build_time_unix": 1629484778549,
            "env_OS_GIT_TREE_STATE": "clean",
            "incomplete": "True",
            "build_0_id": null,
            "build_0_version": null,
            "label_release": "202108201835.p0.git.0cdf732",
            "brew_task_state": "failure",
            "label_io_openshift_build_commit_id": "0cdf732a2cbc425fd74bb7e8793f0d55bba71a39",
            "env_OS_GIT_MINOR": 5,
            "group": "openshift-4.5",
            "dg_commit": "9f0f5eae",
            "brew_image_shas": null,
            "label_io_openshift_build_source_location": "https://github.com/openshift/ironic-inspector-image",
            "build_0_release": null,
            "dg_name": "ironic-inspector",
            "env_OS_GIT_VERSION": "4.5.0-202108201835.p0.git.0cdf732-0cdf732",
            "build_0_source": null,
            "time_iso": "2021-08-20T18:39:38Z",
            "runtime_uuid": 20210820.183632,
            "label_io_openshift_maintainer_subcomponent": "ironic",
            "label_io_openshift_build_commit_url": "https://github.com/openshift/ironic-inspector-image/commit/0cdf732a2cbc425fd74bb7e8793f0d55bba71a39",
            "build_0_name": null,
            "label_io_openshift_maintainer_component": "Bare Metal Hardware Provisioning",
            "build_time_iso": "2021-08-20T18:39:38Z",
            "brew_task_id": 39151665,
            "label_version": "v4.5.0",
            "label_io_openshift_maintainer_product": "OpenShift Container Platform",
            "env_OS_GIT_PATCH": 0,
            "jenkins_job_url": "https://saml.buildvm.openshift.eng.bos.redhat.com:8888/job/hack/job/lmeyer/job/lmeyer-dev/job/dev-build%252Fcustom/",
            "env_OS_GIT_COMMIT": "0cdf732",
            "jenkins_job_name": "hack/lmeyer/lmeyer-dev/dev-build%2Fcustom",
            "label_com_redhat_component": "ironic-inspector-container",
            "dg_qualified_name": "containers/ironic-inspector",
            "label_name": "openshift/ose-ironic-inspector",
            "jenkins_node_name": "master",
            "dg_qualified_key": "containers/ironic-inspector",
            "jenkins_build_url": "https://saml.buildvm.openshift.eng.bos.redhat.com:8888/job/hack/job/lmeyer/job/lmeyer-dev/job/dev-build%252Fcustom/55/",
            "dg_namespace": "containers",
            "brew_faultCode": null,
            "jenkins_build_number": 55,
            "build_0_nvr": null,
            "brew_build_ids": null,
            "label_io_openshift_tags": null,
            "env_KUBE_GIT_TREE_STATE": null,
            "env_KUBE_GIT_MAJOR": null,
            "env_KUBE_GIT_VERSION": null,
            "env_KUBE_GIT_MINOR": null,
            "env_KUBE_GIT_COMMIT": null,
            "label_io_openshift_release_operator": null,
            "label_io_openshift_expose_services": null,
            "label_io_openshift_s2i_scripts_url": null,
            "label_io_openshift_build_versions": null
        }
    ]
}
```
Can filter with individual fields by specifying their name. Eg: ```/api/v1/builds/?build_0_package_id=79812```