# art-dashboard-server

![run-tox badge](https://github.com/openshift-eng/art-dashboard-server/actions/workflows/run_tox.yml/badge.svg)

# Setup Test Environment

## 1. get the base art-dash-server build


you can build it from scratch
```
# only required once unless RPM reqs change
podman build -f Dockerfile.base -t art-dash-server:base --build-arg USERNAME=$USER --build-arg USER_UID=$(id -u) .

# repeat this to update the app as it changes
podman build -f Dockerfile.update -t art-dash-server:latest --build-arg USERNAME=$USER --build-arg USER_UID=$(id -u) .
```
or you can get the build from [cluster](https://console-openshift-console.apps.artc2023.pc3z.p1.openshiftapps.com/k8s/ns/art-dashboard-server/imagestreams/art-dash-server)
```
# after you log in to the cluster on CLI
oc registry login
# pull image
podman pull default-route-openshift-image-registry.apps.artc2023.pc3z.p1.openshiftapps.com/art-dashboard-server/art-dash-server
```

## 2. Create network Env
```
podman network create art-dashboard-network
```

## 3. Setup local database

Start the local DB server using a specific version of MariaDB (10.6.14), as the latest version doesn't include MySQL.
```
podman run --net art-dashboard-network --name mariadb -e MARIADB_ROOT_PASSWORD=secret -e MARIADB_DATABASE=doozer_build -d docker.io/library/mariadb:10.6.14
```

Download the test database as `test.sql`. 
```
# Log in to OpenShift CLI and switch to the art-db project
oc login
oc project art-db

# Get the running DB pod
oc get pods

# Enter the pod
oc exec -it <pod-name> -- /bin/bash

# Inside the pod, dump the 'art_dash' database into a file named test.sql
mysqldump -uroot art_dash > test.sql

# Exit the pod
exit

# Sync the dumped file from the pod to your local machine
oc rsync <pod-name>:/opt/app-root/src/test.sql /path/to/art-dashboard-server
```

Import db into the mariadb container
```
podman cp test.sql mariadb:/test.sql
podman exec -ti mariadb /bin/bash

# Inside the container
mysql -uroot -psecret
CREATE DATABASE art_dash;
exit
mysql -uroot -psecret art_dash < test.sql
```
Password is `secret` as defined in the podman run command.


## 4. Run container

```
OPENSHIFT=$HOME/ART-dash    # create a workspace, clone art-tools and art-dash to this location.

podman run -it --rm -p 8080:8080 --net art-dashboard-network \
-v "$OPENSHIFT/art-dashboard-server":/workspaces/art-dash:cached,z \
-v $OPENSHIFT/art-tools/doozer/:/workspaces/doozer/:cached,z \
-v $OPENSHIFT/art-tools/elliott/:/workspaces/elliott/:cached,z \
-v $HOME/.ssh:/home/$USER/.ssh:ro,cached,z \
-v $HOME/.docker/config.json:/home/$USER/.docker/config.json:ro,cached,z \
-v $HOME/.gitconfig:/home/$USER/.gitconfig:ro,cached,z \
-e RUN_ENV=development \
-e GITHUB_PERSONAL_ACCESS_TOKEN='<your github token>' \
    art-dash-server:latest
```

## 5. Test if it works
```
$curl -i 'http://localhost:8080/api/v1/test'
HTTP/1.1 200 OK
Date: Mon, 22 May 2023 11:51:22 GMT
Server: WSGIServer/0.2 CPython/3.9.9
Content-Type: application/json
Vary: Accept, Origin, Cookie
Allow: GET, OPTIONS
X-Frame-Options: DENY
Content-Length: 50
X-Content-Type-Options: nosniff
Referrer-Policy: same-origin
Cross-Origin-Opener-Policy: same-origin

```
To stop `art-dash-server:latest`, use `Ctrl-C`

To stop mariadb server, run `podman stop mariadb`


## Notes:

- To debug in development, set `DEBUG = True` in `build_interface/settings.py`. But it SHOULD be set to `False` before committing/pushing to remote.
- To test deployment, use the `art-build-dev` namespace. Docs can be found at [art-dash-deployment](https://github.com/openshift-eng/art-config/tree/main/clusters/psi-ocp4/aos-art-web) (Need to be added to our team in Openshift GitHub org)
- Environment variables that is common to both development and production should be defined in `conf/common.env`. The variables in that file is loaded first and then the ones on `prod.env` or `dev.env` depending on the environment.
- It's recommended to set up a kerberos config file similar to the one in this project so that you can easily mount your keytab as shown above. Otherwise, you'll have to `kinit` inside the container everytime. Please make modifications to the volume mount command to reflect the keytab format in your local.
- If an error like `failed to export image: failed to create image: failed to get layer` shows up during container build, re-run the command again.
