# art-dashboard-server

How to run it:

	podman network create art-dashboard-network
	podman run --net art-dashboard-network --name mariadb -e MARIADB_ROOT_PASSWORD=secret -e MARIADB_DATABASE=doozer_build -d docker.io/library/mariadb:latest
	podman build -t art-dashboard-server .
	podman run -it --rm -p 8080:8080 --net art-dashboard-network -v $(pwd):/opt/app-root/src art-dashboard-server

How to use it:

	curl -i 'http://localhost:8080/incident/'

@TODO: fetch more examples from [art-dashboard-ui](https://github.com/openshift/art-dashboard-ui)

Cleaning up:

	podman stop mariadb
	podman rm mariadb
	podman network rm art-dashboard-network
