# ART-API

Dev Base URL: ```http://localhost:8080``` <br>
For Prod URL check `ART_DASH_SERVER_ROUTE` in production build configs.

### GET /api/v1/builds

Prints all the build details. Results are paginated, per page 100 results. <br><br>

Can filter with individual fields by specifying their name. Eg: ```/api/v1/builds/?build_0_package_id=79812```

### GET /api/v1/pipeline-image

Endpoint to get the image pipeline of an image, starting from github, distgit, brew, cdn or delivery repo name.

Request payload:

starting_from: The starting point of the pipeline. Possible values: `github` | `distgit` | `brew` | `cdn`
| `delivery` <br>
name: Name of the package eg: `hypershift` for github, `ose-hypershift-container` for
brew, `openshift4/ose-hypershift-rhel8` for delivery<br>
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

### GET /api/v1/ga-version

Get the Openshift GA version

Request: ``http://art-dash-server-art-build-dev.apps.ocp4.prod.psi.redhat.com/api/v1/ga-version``

Response:

```json
{
  "status": "success",
  "payload": "4.11"
}
```

### GET /api/v1/branch

This endpoint can be used for the following 3 purposes:

- Get all the branches from OCP build data GitHub repo using the query param ``type=all``

Request: ``http://art-dash-server-art-build-dev.apps.ocp4.prod.psi.redhat.com//release/branch/?type=all``

Response:

```json
[
  {
    "name": "openshift-4.13",
    "version": "4.13",
    "priority": 0,
    "extra_details": {
      "name": "openshift-4.13",
      "commit": {
        "sha": "cd1d757c2327921049eddc51705e9579e0a76278",
        "url": "https://api.github.com/repos/openshift/ocp-build-data/commits/cd1d757c2327921049eddc51705e9579e0a76278"
      },
      "protected": true
    }
  }
]
```

- Get the current and previous advisories for a particular branch with the
  params ``type=openshift_branch_advisory_ids&branch=openshift-4.11``

Request: ``http://art-dash-server-art-build-dev.apps.ocp4.prod.psi.redhat.com//release/branch/?type=openshift_branch_advisory_ids&branch=openshift-4.11``

Response:

```json
{
  "current": {
    "extras": 100,
    "image": 101,
    "metadata": 102,
    "rpm": 103
  },
  "previous": {
    "extras": 99,
    "image": 98,
    "metadata": 97,
    "rpm": 96
  }
}
```

- Get the advisory details of a particular advisory using the params ``type=advisory&id=100``

Request: ``http://art-dash-server-art-build-dev.apps.ocp4.prod.psi.redhat.com//errata/advisory/?type=advisory&id=100``

Response:

```json
{
  "status": "success",
  "message": "Data is ready.",
  "data": {
    "advisory_details": [
      {
        ...
      }
    ],
    "bugs": [],
    "bug_summary": []
  }
}
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

### GET /api/v1/rpms-images-fetcher

This endpoint fetches and returns the rpms and images data for a specific release from the GitHub repository. The release corresponds to a branch in the repository.

Request payload:

release: The name of the release (branch in the repository).

eg:

Request: `localhost:8080/api/v1/rpms-images-fetcher?release=openshift-4.11`

Response:

```json
{
    "status": "success",
    "payload": [
        {
            "branch": "openshift-4.11",
            "rpms_in_distgit": [...],
            "images_in_distgit": [...]
        }
    ]
}
```