import requests
import unittest

# Test deployment at art-build-dev Openshift namespace
# If local, set SERVER = "http://localhost:8080"
SERVER = "http://art-dash-server-art-build-dev.apps.ocp4.prod.psi.redhat.com"
API = f"{SERVER}/api/v1"


class TestGithub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        params = {
            "starting_from": "github",
            "name": "metallb",
            "version": "4.10"
        }
        endpoint = f"{API}/pipeline-image"
        response = requests.get(endpoint, params=params)
        cls.response = response
        cls.json = response.json()

    def test_1(self):
        assert self.response.status_code == 200

    def test_2(self):
        assert self.json.get('status') == "success"

    def test_3(self):
        assert self.json.get('payload') != {}

    def test_4(self):
        distgit_name = self.json['payload']['distgit'][0]['distgit_repo_name']
        assert distgit_name is not None

    def test_5(self):
        brew_name = self.json['payload']['distgit'][0]['brew']['brew_package_name']
        assert brew_name is not None

    def test_6(self):
        cdn_repo_name = self.json['payload']['distgit'][0]['brew']['cdn'][0]['cdn_repo_name']
        assert cdn_repo_name is not None

    def test_7(self):
        distgit = self.json['payload']['distgit'][0]['brew']['cdn'][0]['delivery']['delivery_repo_name']
        assert distgit is not None


class TestDistgit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        params = {
            "starting_from": "distgit",
            "name": "ose-metallb",
            "version": "4.10"
        }
        endpoint = f"{API}/pipeline-image"
        response = requests.get(endpoint, params=params)
        cls.response = response
        cls.json = response.json()

    def test_1(self):
        assert self.response.status_code == 200

    def test_2(self):
        assert self.json.get('status') == "success"

    def test_3(self):
        assert self.json.get('payload') != {}

    def test_4(self):
        distgit_name = self.json['payload']['distgit'][0]['distgit_repo_name']
        assert distgit_name is not None

    def test_5(self):
        brew_name = self.json['payload']['distgit'][0]['brew']['brew_package_name']
        assert brew_name is not None

    def test_6(self):
        cdn_repo_name = self.json['payload']['distgit'][0]['brew']['cdn'][0]['cdn_repo_name']
        assert cdn_repo_name is not None

    def test_7(self):
        distgit = self.json['payload']['distgit'][0]['brew']['cdn'][0]['delivery']['delivery_repo_name']
        assert distgit is not None


class TestBrew(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        params = {
            "starting_from": "brew",
            "name": "ose-metallb-container",
            "version": "4.10"
        }
        endpoint = f"{API}/pipeline-image"
        response = requests.get(endpoint, params=params)
        cls.response = response
        cls.json = response.json()

    def test_1(self):
        assert self.response.status_code == 200

    def test_2(self):
        assert self.json.get('status') == "success"

    def test_3(self):
        assert self.json.get('payload') != {}

    def test_4(self):
        distgit_name = self.json['payload']['distgit'][0]['distgit_repo_name']
        assert distgit_name is not None

    def test_5(self):
        brew_name = self.json['payload']['distgit'][0]['brew']['brew_package_name']
        assert brew_name is not None

    def test_6(self):
        cdn_repo_name = self.json['payload']['distgit'][0]['brew']['cdn'][0]['cdn_repo_name']
        assert cdn_repo_name is not None

    def test_7(self):
        distgit = self.json['payload']['distgit'][0]['brew']['cdn'][0]['delivery']['delivery_repo_name']
        assert distgit is not None


class TestCdn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        params = {
            "starting_from": "cdn",
            "name": "redhat-openshift-tech-preview-metallb-rhel8",
            "version": "4.10"
        }
        endpoint = f"{API}/pipeline-image"
        response = requests.get(endpoint, params=params)
        cls.response = response
        cls.json = response.json()

    def test_1(self):
        assert self.response.status_code == 200

    def test_2(self):
        assert self.json.get('status') == "success"

    def test_3(self):
        assert self.json.get('payload') != {}

    def test_4(self):
        distgit_name = self.json['payload']['distgit'][0]['distgit_repo_name']
        assert distgit_name is not None

    def test_5(self):
        brew_name = self.json['payload']['distgit'][0]['brew']['brew_package_name']
        assert brew_name is not None

    def test_6(self):
        cdn_repo_name = self.json['payload']['distgit'][0]['brew']['cdn'][0]['cdn_repo_name']
        assert cdn_repo_name is not None

    def test_7(self):
        distgit = self.json['payload']['distgit'][0]['brew']['cdn'][0]['delivery']['delivery_repo_name']
        assert distgit is not None


class TestDelivery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        params = {
            "starting_from": "delivery",
            "name": "openshift-tech-preview/metallb-rhel8",
            "version": "4.10"
        }
        endpoint = f"{API}/pipeline-image"
        response = requests.get(endpoint, params=params)
        cls.response = response
        cls.json = response.json()

    def test_1(self):
        assert self.response.status_code == 200

    def test_2(self):
        assert self.json.get('status') == "success"

    def test_3(self):
        assert self.json.get('payload') != {}

    def test_4(self):
        distgit_name = self.json['payload']['distgit'][0]['distgit_repo_name']
        assert distgit_name is not None

    def test_5(self):
        brew_name = self.json['payload']['distgit'][0]['brew']['brew_package_name']
        assert brew_name is not None

    def test_6(self):
        cdn_repo_name = self.json['payload']['distgit'][0]['brew']['cdn'][0]['cdn_repo_name']
        assert cdn_repo_name is not None

    def test_7(self):
        distgit = self.json['payload']['distgit'][0]['brew']['cdn'][0]['delivery']['delivery_repo_name']
        assert distgit is not None
