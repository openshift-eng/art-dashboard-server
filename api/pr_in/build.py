import os

import requests
from util import get_commits_after

API = f"{os.environ['ART_DASH_SERVER_ROUTE']}/api/v1"


def commit_in_build(version, commit, task_state):
    params = {
        'group': f"openshift-{version}",
        'label_io_openshift_build_commit_id': commit,
        'brew_task_state': f'{task_state}'
    }
    url = f"{API}/builds/"
    response = requests.get(url, params=params)
    return response.json()


def pr_in_build(repo, version, commit):
    commits_after = get_commits_after(repo, commit, version)
    for commit in commits_after:
        response = commit_in_build(version, commit, 'success')
        if response['count'] > 0:
            builds = response['results']
            build_ids = [x['build_0_id'] for x in builds]
            return build_ids
