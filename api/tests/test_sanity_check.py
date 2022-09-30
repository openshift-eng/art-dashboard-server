import requests
import unittest

# Test deployment at art-build-dev Openshift namespace
API = "http://art-dash-server-art-build-dev.apps.ocp4.prod.psi.redhat.com/api/v1"


class TestSanityCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        endpoint = f"{API}/test"
        cls.response = requests.get(endpoint)

    def test_1(self):
        assert self.response.status_code == 200
