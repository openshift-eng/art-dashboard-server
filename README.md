# art-dashboard-server

Setup

    podman network create art-dashboard-network
    podman build -f Dockerfile.base -t art-dash-server:base .

Build

    podman build -f Dockerfile.update -t art-dash-server:latest .

Start DB server

    podman run --net art-dashboard-network --name mariadb -e MARIADB_ROOT_PASSWORD=secret -e MARIADB_DATABASE=doozer_build -d docker.io/library/mariadb:latest

Run container
    
    OPENSHIFT=$HOME/ART-PyCharm-Projects    # CLone doozer, elliot and art-dash to this location.

    podman run -it --rm -p 8080:8080 --net art-dashboard-network \
        -v $(pwd):/workspaces/art-dash \
        -v $OPENSHIFT/doozer/:/workspaces/doozer/:cached,z \
        -v $OPENSHIFT/elliott/:/workspaces/elliott/:cached,z \
        -v $HOME/.ssh:/home/$USER/.ssh:ro,cached,z \
        -v $HOME/.docker/config.json:/home/$USER/.docker/config.json:ro,cached,z \
        -v $HOME/.gitconfig:/home/$USER/.gitconfig:ro,cached,z \
        -v $HOME/.vim/:/home/$USER/.vim/:ro,cached,z \
        -v $HOME/.vimrc:/home/$USER/.vimrc:ro,cached,z \
        -e RUN_ENV=development \
        -e GITHUB_PERSONAL_ACCESS_TOKEN='<your github token>' \
        -v /tmp/krb5cc_1000:/tmp/krb5cc_1000 \    # Optional. Will have to kinit inside the container, if removing this line.
            art-dash-server:latest


Test

	curl -i 'http://localhost:8080/api/v1/test'

To stop `art-dash-server:latest`, use `Ctrl-C`and to stop mariadb server, run `podman stop mariadb`


Notes:

- To debug in development, set `DEBUG = True` in `build_interface/settings.py`. But it SHOULD be set to `False` before committing/pushing to remote.
- To test deployment, use the `art-build-dev` namespace. Docs can be found at [art-dash-deployment](https://github.com/openshift-eng/art-config/tree/main/clusters/psi-ocp4/aos-art-web) (Need to be added to our team in Openshift GitHub org)
- Environment variables that is common to both development and production should be defined in `conf/common.env`. The variables in that file is loaded first and then the ones on `prod.env` or `dev.env` depending on the environment.
- Test an `oc` command inside the container to make sure that it works. Otherwise, copy the `oc login` from `app.ci` and run it followed by `oc registry login`, inside the container.
- It's recommended to set up a kerberos config file similar to the one in this project so that you can easily mount your keytab as shown above. Otherwise, you'll have to `kinit` inside the container everytime. Please make
modifications to the volume mount command to reflect the keytab format in your local.
- If an error like `failed to export image: failed to create image: failed to get layer` shows up during container build, re-run the command again.