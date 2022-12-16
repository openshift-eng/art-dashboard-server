# ART-API

Dev Base URL: ```http://localhost:8080``` <br>
For Prod URL check `ART_DASH_SERVER_ROUTE` in production build configs.

### GET /api/v1/builds
Prints all the build details. Results are paginated, per page 100 results. <br><br>

Can filter with individual fields by specifying their name. Eg: ```/api/v1/builds/?build_0_package_id=79812```

### GET /api/v1/pipeline-image

Endpoint to get the image pipeline of an image, starting from github, distgit, brew, cdn or delivery repo name.

Request payload:

starting_from: The starting point of the pipeline. Possible values: `github` | `distgit` | `brew` | `cdn` | `delivery` <br>
name: Name of the package eg: `hypershift` for github, `ose-hypershift-container` for brew, `openshift4/ose-hypershift-rhel8` for delivery<br>
version: Openshift version. Eg: `4.10`

eg: 

Request: `localhost:8080/api/v1/pipeline-image?starting_from=github&name=hypershift&version=4.10`

Response:

```json
{
    "status": "success",
    "payload": {
        "openshift_version": "",
        "github_repo": "",
        "upstream_github_url": "",
        "private_github_url": "",
        "distgit": [
            {
                "distgit_repo_name": "",
                "distgit_url": "",
                "brew": {
                    "brew_id": ,
                    "brew_build_url": "",
                    "brew_package_name": "",
                    "bundle_component": "",
                    "bundle_distgit": "",
                    "payload_tag": "",
                    "cdn": [
                        {
                            "cdn_repo_id": ,
                            "cdn_repo_name": "",
                            "cdn_repo_url": "",
                            "variant_name": "",
                            "variant_id": ,
                            "delivery": {
                                "delivery_repo_id": "",
                                "delivery_repo_name": "",
                                "delivery_repo_url": ""}}]}}]}}
```

### GET /api/v1/test

Test endpoint to check if server is deployed correctly, both local and in production.

Request: ``http://art-dash-server-art-build-dev.apps.ocp4.prod.psi.redhat.com/api/v1/test``

Response:
```json
{
    "status": "success",
    "payload": "Setup successful"
}
```