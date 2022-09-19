# ART-API

Prod Base URL: ```http://art-dash-server-aos-art-web.apps.ocp4.prod.psi.redhat.com```<br>
Dev Base URL: ```http://localhost:8080```

### GET /api/v1/builds
Prints all the build details. Results are paginated, per page 100 results. <br><br>

Can filter with individual fields by specifying their name. Eg: ```/api/v1/builds/?build_0_package_id=79812```

### GET /api/v1/pipline-image

Endpoint to get the image pipeline of an image, starting from github, distgit, brew, cdn or delivery repo name.

Request payload:

starting_from: The starting point of the pipeline, eg github, if we are starting from github
name: Github repo name | distgit name | brew name | cdn name | delivery repo name
version: Openshift version

Response is returned in JSON format.