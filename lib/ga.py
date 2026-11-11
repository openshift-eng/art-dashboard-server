"""OpenShift GA series discovery, independent of application/runtime imports."""
import os
import re

import requests


def get_openshift_ga_version():
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    response = requests.get(
        "https://api.github.com/repos/openshift/cincinnati-graph-data/git/trees/master?recursive=1",
        headers={"Authorization": f"token {token}"} if token else {}, timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("truncated"):
        raise requests.RequestException("The OpenShift channel listing is incomplete")
    versions = []
    for entry in data.get("tree", []):
        match = re.fullmatch(r"channels/fast-(\d+)\.(\d+)\.yaml", entry.get("path", ""))
        if match:
            versions.append(tuple(map(int, match.groups())))
    if not versions:
        raise requests.RequestException("No OpenShift fast channels were returned")
    major, minor = max(versions)
    return f"{major}.{minor}"
