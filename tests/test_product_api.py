import unittest
from unittest.mock import patch

import requests
from django.conf import settings

if not settings.configured:
    settings.configure(SECRET_KEY="test-only", REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": [], "UNAUTHENTICATED_USER": None,
    })

from rest_framework.test import APIRequestFactory

from api import product_views


class ProductAPITests(unittest.TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_catalog(self):
        response = product_views.products(self.factory.get("/products/"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p["id"] for p in response.data], ["openshift", "acm", "mce"])

    @patch.object(product_views, "get_product_ga", return_value={"version": "5.0", "group": "acm-5.0"})
    def test_ga_passes_product_and_returns_metadata(self, get):
        response = product_views.ga(self.factory.get("/products/acm/ga/"), "acm")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["group"], "acm-5.0")
        get.assert_called_once_with("acm")

    def test_unknown_ga_product_returns_400(self):
        response = product_views.ga(self.factory.get("/products/unknown/ga/"), "unknown")
        self.assertEqual(response.status_code, 400)

    @patch.object(product_views, "get_product_ga", side_effect=requests.HTTPError("Unavailable"))
    def test_ga_upstream_failure_returns_502(self, get):
        response = product_views.ga(self.factory.get("/products/acm/ga/"), "acm")
        self.assertEqual(response.status_code, 502)

    def test_wrong_product_group_returns_400_without_network_access(self):
        response = product_views.releases(self.factory.get("/products/acm/releases/?group=mce-5.0"), "acm")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    @patch.object(product_views, "get_product_release")
    def test_detail_passes_product_group_and_assembly(self, get):
        get.return_value = {"version": "2.17.4", "shipments": []}
        response = product_views.release_detail(self.factory.get("/products/acm/release/?group=acm-2.17&assembly=2.17.4"), "acm")
        self.assertEqual(response.status_code, 200)
        get.assert_called_once_with("acm", "acm-2.17", "2.17.4")

    @patch.object(product_views, "get_product_release", side_effect=LookupError("Release not recorded"))
    def test_missing_release_returns_404(self, get):
        response = product_views.release_detail(self.factory.get("/products/acm/release/?group=acm-2.17&assembly=bad"), "acm")
        self.assertEqual(response.status_code, 404)

    @patch.object(product_views, "get_product_releases", side_effect=requests.HTTPError("Forbidden"))
    def test_upstream_failure_returns_502(self, get):
        response = product_views.releases(self.factory.get("/products/acm/releases/?group=acm-2.17"), "acm")
        self.assertEqual(response.status_code, 502)
        self.assertIn("temporarily unavailable", response.data["error"])


if __name__ == "__main__":
    unittest.main()
