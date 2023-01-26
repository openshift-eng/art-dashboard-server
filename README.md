# art-dashboard-server

![run-tox badge](https://github.com/openshift-eng/art-dashboard-server/actions/workflows/run_tox.yml/badge.svg)

Build
    
    # only required once unless RPM reqs change
    podman build -f Dockerfile.base -t art-dash-server:base --build-arg USERNAME=$USER --build-arg USER_UID=$(id -u) .
    
    # repeat this to update the app as it changes
    podman build -f Dockerfile.update -t art-dash-server:latest --build-arg USERNAME=$USER --build-arg USER_UID=$(id -u) .

Create podman network

`podman network create art-dashboard-network`

Start DB server

    podman run --net art-dashboard-network --name mariadb -e MARIADB_ROOT_PASSWORD=secret -e MARIADB_DATABASE=doozer_build -d docker.io/library/mariadb:latest

Download the test database as `test.sql`. Copy the file into the mariadb container using `sudo docker cp test.sql mariadb:.`
bash into the mariadb container and run `mysql -u root -p < test.sql`. Password is `secret` as defined in the podman run command.


Run container
    
    OPENSHIFT=$HOME/ART-PyCharm-Projects    # CLone doozer, elliot and art-dash to this location.

    podman run -it --rm -p 8080:8080 --net art-dashboard-network \
        -v "$OPENSHIFT/art-dashboard-server":/workspaces/art-dash:cached,z \
        -v $OPENSHIFT/doozer/:/workspaces/doozer/:cached,z \
        -v $OPENSHIFT/elliott/:/workspaces/elliott/:cached,z \
        -v $HOME/.ssh:/home/$USER/.ssh:ro,cached,z \
        -v $HOME/.docker/config.json:/home/$USER/.docker/config.json:ro,cached,z \
        -v $HOME/.gitconfig:/home/$USER/.gitconfig:ro,cached,z \
        -e RUN_ENV=development \
        -e GITHUB_PERSONAL_ACCESS_TOKEN='<your github token>' \
            art-dash-server:latest


Test

	curl -i 'http://localhost:8080/api/v1/test'

To stop `art-dash-server:latest`, use `Ctrl-C`and to stop mariadb server, run `podman stop mariadb`


Notes:

- To debug in development, set `DEBUG = True` in `build_interface/settings.py`. But it SHOULD be set to `False` before committing/pushing to remote.
- To test deployment, use the `art-build-dev` namespace. Docs can be found at [art-dash-deployment](https://github.com/openshift-eng/art-config/tree/main/clusters/psi-ocp4/aos-art-web) (Need to be added to our team in Openshift GitHub org)
- Environment variables that is common to both development and production should be defined in `conf/common.env`. The variables in that file is loaded first and then the ones on `prod.env` or `dev.env` depending on the environment.
- It's recommended to set up a kerberos config file similar to the one in this project so that you can easily mount your keytab as shown above. Otherwise, you'll have to `kinit` inside the container everytime. Please make
modifications to the volume mount command to reflect the keytab format in your local.
- If an error like `failed to export image: failed to create image: failed to get layer` shows up during container build, re-run the command again.