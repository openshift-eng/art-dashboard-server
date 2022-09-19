import requests


def pr_merge_commit(repo, pr):
    response = requests.get(f"https://api.github.com/repos/openshift/{repo}/pulls/{pr}")
    return response.json().get("merge_commit_sha")


def get_branches(repo):
    response = requests.get(f"https://api.github.com/repos/openshift/{repo}/branches")
    return response.json()


def get_branch_ref(repo, version):
    branches = get_branches(repo)
    for data in branches:
        if data['name'] == f"release-{version}":
            return data['commit']['sha']


def get_commit_time(repo, commit):
    response = requests.get(f"https://api.github.com/repos/openshift/{repo}/commits/{commit}")
    return response.json()['commit']['committer']['date']


def get_commits_after(repo, commit, version):
    """
    Function to return commits in a repo from the given time (includes the current commit).
    """
    branch_ref = get_branch_ref(repo, version)
    datetime = get_commit_time(repo, commit)
    response = requests.get(
        f"https://api.github.com/repos/openshift/{repo}/commits?sha={branch_ref}&since={datetime}")

    result = []
    for data in response.json():
        result.append(data['sha'])
    return result[::-1]
