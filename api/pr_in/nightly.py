import requests
import json
from api import util as api_util
from api.pr_in import util
from api import util as util_main


@util_main.refresh_krb_auth
def commit_in_pullspec(commits, pull_spec, repo):
    rc, stdout, stderr = api_util.cmd_gather(f"oc adm release info {pull_spec} --commits -o json")

    if not rc:
        data = json.loads(stdout)
        for tag in data['references']['spec']['tags']:
            if tag['annotations']['io.openshift.build.source-location'] == f"https://github.com/openshift/{repo}":
                commit_id = tag['annotations']['io.openshift.build.commit.id']
                if commit_id in commits:  # Is checked in order
                    return commit_id
    else:
        raise Exception("oc command error")

    return None


def get_nightlies(arch, version):
    url = f"https://{arch}.ocp.releases.ci.openshift.org/api/v1/releasestream/{version}.0-0.nightly/tags"
    response = requests.get(url)
    return response.json().get("tags")


def pr_in_nightly(arch, version, repo, pr, commit):
    """ Driver function """
    try:
        if not commit:
            commit = util.pr_merge_commit(repo, pr)
        if not commit:
            return {
                       "status": "error",
                       "payload": "Invalid pull request"
                   }, 404

        commits_after = util.get_commits_after(repo, commit, version)[::-1]  # Check from the oldest commit to newest
        tags = get_nightlies(arch, version)[::-1]  # Check from the oldest nightly to the newest
        if not tags:
            return {
                       "status": "error",
                       "payload": "Invalid architecture or openshift version"
                   }, 404

        for tag in tags:
            pull_spec = tag['pullSpec']
            commit_in_nightly = commit_in_pullspec(commits_after, pull_spec, repo)
            if commit_in_nightly:
                return {
                           "status": "success",
                           "payload": {
                               'nightly': tag['name'],
                               'nightly_url': f"https://{arch}.ocp.releases.ci.openshift.org/releasestream/{version}.0-0.nightly/release/{tag['name']}",
                               'commit_sha': commit_in_nightly,
                               'repo': repo,
                               'commit_url': f"https://github.com/openshift/{repo}/commit/{commit}"
                           }
                       }, 200

        return {
                   "status": "success",
                   "payload": {}
               }, 200

    except Exception as e:
        print(e)
        return {
                   "status": "error",
                   "payload": {}
               }, 500
