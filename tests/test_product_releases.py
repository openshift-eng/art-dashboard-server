import os
import unittest
from unittest.mock import Mock, patch
from urllib.parse import unquote_plus

import requests

from lib import ga
from lib import gitlab_requests as gitlab
from lib import product_releases as releases
from lib.products import product_for_group, validate_product_group, version_key

MR = "https://gitlab.cee.redhat.com/hybrid-platforms/art/ocp-shipment-data/-/merge_requests/1133"


def shipment(product="rhacm2", group="acm-2.17", application="acm-2-17", fbc=False, shipped=False):
    return {"shipment": {
        "metadata": {"product": product, "group": group, "assembly": "2.17.4", "application": application, "fbc": fbc},
        "data": None if fbc else {"releaseNotes": {"type": "RHSA", "live_id": 1234}},
        "environments": {
            "stage": {"releasePlan": "stage", "result": {"pipeline": "https://example.com/stage"}},
            "prod": {"releasePlan": "prod", "result": {"pipeline": "https://example.com/prod"} if shipped else None},
        },
    }}


class ShipmentTests(unittest.TestCase):
    def setUp(self):
        self.mr = {"state": "opened", "sha": "source-sha", "source_project_id": 42, "target_project_id": 42,
                   "source_branch": "custom-shipment-name", "head_pipeline": {"status": "success"}}
        self.files = {
            "shipment/rhacm2/acm-2.17/acm-2-17/prod/2.17.4.image.100.yaml": shipment(),
            "shipment/rhacm2/acm-2.17/acm-2-17-fbc-4-20/prod/2.17.4.fbc.ocp4.20.10001.yaml": shipment(application="acm-2-17-fbc-4-20", fbc=True),
            "shipment/rhacm2/acm-2.17/acm-2-17-fbc-4-21/prod/2.17.4.fbc.ocp4.21.10002.yaml": shipment(application="acm-2-17-fbc-4-21", fbc=True, shipped=True),
        }
        self.patches = [
            patch.object(gitlab, "_get_mr_metadata", side_effect=lambda *args: self.mr),
            patch.object(gitlab, "_get_mr_approval_state", return_value={"rules": [{"name": "Docs", "approved": True, "approved_by": []}]}),
            patch.object(gitlab, "_get_mr_files", side_effect=lambda *args: list(self.files)),
            patch.object(gitlab, "_get_file_content", side_effect=lambda project, path, ref: self.files[unquote_plus(path)]),
        ]
        self.mocks = [p.start() for p in self.patches]
        self.addCleanup(patch.stopall)

    def test_multiple_fbc_shipments_and_partial_production(self):
        result = gitlab.get_shipment_status(MR, "acm-2.17", "2.17.4")
        self.assertEqual(result["status"], "Partially shipped")
        self.assertEqual(len(result["shipments"]), 3)
        self.assertEqual(sum(s["kind"] == "fbc" for s in result["shipments"]), 2)
        self.assertEqual(result["approvals"]["Docs"], {"approved": True, "approved_by": "", "required": True})
        self.assertFalse(next(s for s in result["shipments"] if s["kind"] == "fbc")["advisory_required"])

    def test_merged_mr_uses_merge_commit_and_target_project(self):
        self.mr.update(state="merged", merge_commit_sha="merge-sha", source_project_id=None)
        result = gitlab.get_shipment_status(MR, "acm-2.17", "2.17.4")
        self.assertNotIn("error", result)
        self.assertTrue(all(call.args[0] == "42" and call.args[2] == "merge-sha" for call in self.mocks[3].call_args_list))

    def test_wrong_metadata_is_visible_and_does_not_report_success(self):
        self.files[next(iter(self.files))]["shipment"]["metadata"]["product"] = "multicluster-engine"
        result = gitlab.get_shipment_status(MR, "acm-2.17", "2.17.4")
        self.assertEqual(result["status"], "Unknown")
        self.assertTrue(any(s.get("error") for s in result["shipments"]))

    def test_gitlab_failure_is_not_pending(self):
        self.mocks[0].side_effect = requests.HTTPError("401 Unauthorized")
        self.assertIn("error", gitlab.get_shipment_status(MR, "acm-2.17", "2.17.4"))

    def test_different_product_and_assembly_files_are_ignored(self):
        self.files = {"shipment/ocp/openshift-4.21/openshift-4-21/prod/4.21.42.image.1.yaml": {}}
        self.assertIn("error", gitlab.get_shipment_status(MR, "acm-2.17", "2.17.4"))

    def test_missing_merge_revision_is_an_error(self):
        self.mr.update(state="merged", sha=None)
        self.assertIn("error", gitlab.get_shipment_status(MR, "acm-2.17", "2.17.4"))

    def test_fast_forward_merge_uses_immutable_head_sha(self):
        self.mr.update(state="merged")
        self.assertNotIn("error", gitlab.get_shipment_status(MR, "acm-2.17", "2.17.4"))
        self.assertTrue(all(call.args[2] == "source-sha" for call in self.mocks[3].call_args_list))

    def test_malformed_shipment_is_a_visible_row_error(self):
        self.files[next(iter(self.files))] = None
        result = gitlab.get_shipment_status(MR, "acm-2.17", "2.17.4")
        self.assertEqual(result["status"], "Unknown")
        self.assertTrue(any(s.get("error") for s in result["shipments"]))

    def test_mce_canonical_product(self):
        self.files = {"shipment/multicluster-engine/mce-2.17/mce-2-17/prod/2.17.4.image.100.yaml":
                      shipment(product="multicluster-engine", group="mce-2.17", application="mce-2-17", shipped=True)}
        self.assertEqual(gitlab.get_shipment_status(MR, "mce-2.17", "2.17.4")["status"], "SHIPPED_LIVE")

    def test_open_mr_uses_source_project_and_immutable_sha(self):
        self.mr["source_project_id"] = 99
        gitlab.get_shipment_status(MR, "acm-2.17", "2.17.4")
        self.assertTrue(all(call.args[0] == "99" and call.args[2] == "source-sha" for call in self.mocks[3].call_args_list))

    def test_skipped_staging_is_not_success(self):
        self.assertEqual(gitlab._environment_status({"releasePlan": "Skipped"})["status"], "Skipped")
        self.assertEqual(gitlab._environment_status(None)["status"], "Not configured")
        self.assertEqual(gitlab._shipment_summary([{"stage": {"status": "Skipped"}, "prod": {"status": "Not started"}}], "opened"), "Stage skipped")


class ProductReleaseTests(unittest.TestCase):
    def setUp(self):
        releases._metadata_cache.clear()
        releases._release_cache.clear()
        releases._ga_cache.clear()
        self.env = patch.dict(os.environ, {"GITHUB_PERSONAL_ACCESS_TOKEN": "test-placeholder"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_product_group_validation(self):
        self.assertEqual(product_for_group("acm-5.0")["shipment_product"], "rhacm2")
        self.assertEqual(product_for_group("mce-5.1")["shipment_product"], "multicluster-engine")
        with self.assertRaises(ValueError):
            validate_product_group("acm", "mce-5.0")

    def test_release_ordering(self):
        values = ["stream", "4.21.9", "4.21.42", "4.21.0-rc.1", "4.21.0"]
        self.assertEqual(sorted(values, key=version_key, reverse=True),
                         ["4.21.42", "4.21.9", "4.21.0", "4.21.0-rc.1", "stream"])

    @patch.object(releases, "_build_data_branches")
    def test_group_filtering_and_numeric_sort(self, branches):
        branches.return_value = [{"name": g} for g in ["mce-2.9", "mce-2.17", "mce-5.0", "mce-5.0-test", "acm-5.0"]]
        self.assertEqual(releases.get_product_groups("mce"), ["mce-5.0", "mce-2.17", "mce-2.9"])

    @patch.object(releases, "get_shipment_status")
    @patch.object(releases, "_build_data_yaml")
    @patch.object(releases, "get_product_groups")
    def test_layered_ga_skips_empty_groups_without_reading_shipments(self, groups, data, shipment_status):
        for product in ("acm", "mce"):
            with self.subTest(product=product):
                groups.return_value = [f"{product}-5.1", f"{product}-5.0", f"{product}-2.17"]
                data.side_effect = [{"releases": {}}, {"releases": {"5.0.0": {"assembly": {"type": "stream"}}}}]
                result = releases.get_product_ga(product)
                self.assertEqual(result, {"version": "5.0", "group": f"{product}-5.0", "source": "build-data-releases"})
                self.assertEqual(data.call_args.args, (f"{product}-5.0", "releases.yml"))
                # A successful GA lookup is cached independently of shipment data.
                self.assertEqual(releases.get_product_ga(product), result)
        self.assertEqual(data.call_count, 4)
        shipment_status.assert_not_called()

    @patch.object(releases, "_build_data_yaml")
    @patch.object(releases, "get_product_groups", return_value=["acm-5.1", "acm-5.0", "acm-2.17"])
    def test_no_ga_for_missing_null_or_empty_release_mappings(self, groups, data):
        data.side_effect = [{}, {"releases": None}, {"releases": {}}]
        self.assertEqual(releases.get_product_ga("acm"),
                         {"version": None, "group": None, "source": "build-data-releases"})

    @patch.object(releases, "_build_data_yaml")
    @patch.object(releases, "get_product_groups", return_value=["mce-5.1", "mce-5.0"])
    def test_ga_upstream_errors_do_not_fall_back_or_get_cached(self, groups, data):
        data.side_effect = requests.HTTPError("Unavailable")
        for _ in range(2):
            with self.assertRaises(requests.HTTPError):
                releases.get_product_ga("mce")
        self.assertEqual(data.call_count, 2)
        self.assertTrue(all(call.args[0] == "mce-5.1" for call in data.call_args_list))

    @patch.object(releases, "_build_data_yaml", return_value={"releases": ["5.0.0"]})
    @patch.object(releases, "get_product_groups", return_value=["acm-5.0"])
    def test_malformed_ga_mapping_is_an_error(self, groups, data):
        with self.assertRaises(TypeError):
            releases.get_product_ga("acm")

    @patch.object(releases, "get_product_groups")
    @patch.object(releases, "get_openshift_ga_version", return_value="5.0")
    def test_openshift_retains_cincinnati_ga_source(self, version, groups):
        self.assertEqual(releases.get_product_ga("openshift"),
                         {"version": "5.0", "group": "openshift-5.0", "source": "cincinnati-fast-channel"})
        groups.assert_not_called()

    @patch.object(ga.requests, "get")
    def test_cincinnati_fast_channels_use_numeric_version_order(self, get):
        get.return_value.json.return_value = {"tree": [{"path": path} for path in (
            "channels/fast-4.9.yaml", "channels/fast-4.21.yaml", "channels/fast-5.0.yaml",
            "channels/stable-5.1.yaml", "channels/fast-5.2-candidate.yaml",
        )]}
        self.assertEqual(ga.get_openshift_ga_version(), "5.0")

    @patch.object(ga.requests, "get")
    def test_missing_or_truncated_cincinnati_channels_are_errors(self, get):
        for payload in ({"tree": []}, {"truncated": True, "tree": [{"path": "channels/fast-5.0.yaml"}]}):
            get.return_value.json.return_value = payload
            with self.assertRaises(requests.RequestException):
                ga.get_openshift_ga_version()

    @patch.object(releases, "PRODUCTS", {"acm": {}})
    @patch.object(releases, "get_product_release", return_value={"version": "5.0.0"})
    @patch.object(releases, "get_product_releases", return_value=[{"version": "5.0.0"}])
    @patch.object(releases, "get_product_ga", return_value={"version": "5.0", "group": "acm-5.0"})
    def test_overview_uses_ga_group(self, product_ga, listing, detail):
        result = releases.get_products_overview()
        self.assertEqual(result[0]["group"], "acm-5.0")
        listing.assert_called_once_with("acm", "acm-5.0")
        detail.assert_called_once_with("acm", "acm-5.0", "5.0.0")

    @patch.object(releases, "_build_data_yaml")
    def test_mr_pointer_and_assembly_inheritance(self, data):
        data.side_effect = [{"product": "rhacm2"}, {"releases": {
            "2.17.3": {"assembly": {"type": "standard", "group": {"release_jira": "ACM-123", "shipment": {"mr": MR}}}},
            "2.17.4": {"assembly": {"type": "standard", "basis": {"assembly": "2.17.3"}, "group": {"shipment": {"mr": MR + "4"}}}},
            "test": {"assembly": {"type": "custom"}},
            "stream": {"assembly": {"type": "stream"}},
        }}]
        result = releases.get_product_releases("acm", "acm-2.17")
        self.assertEqual([r["version"] for r in result], ["2.17.4", "2.17.3"])
        self.assertEqual(result[0]["shipment_url"], MR + "4")
        self.assertEqual(result[0]["jira"], "ACM-123")

    @patch.object(releases, "_build_data_yaml")
    def test_null_release_mapping_is_empty(self, data):
        data.side_effect = [{"product": "multicluster-engine"}, {"releases": None}]
        self.assertEqual(releases.get_product_releases("mce", "mce-5.1"), [])

    @patch.object(releases, "_build_data_yaml")
    def test_old_openshift_advisories_preserved(self, data):
        data.side_effect = [{"advisories": {"image": 123}}, {}]
        result = releases.get_product_releases("openshift", "openshift-3.11")
        self.assertEqual(result[0]["advisories"], {"image": 123})

    @patch.object(releases, "_build_data_yaml")
    def test_wrong_group_product_rejected(self, data):
        data.return_value = {"product": "multicluster-engine"}
        with self.assertRaises(ValueError):
            releases.get_product_releases("acm", "acm-5.0")

    @patch.object(releases, "get_shipment_status")
    @patch.object(releases, "get_product_releases")
    def test_upstream_failure_is_not_cached(self, listing, status):
        listing.return_value = [{"version": "5.0.0", "shipment_url": MR, "advisories": {}}]
        status.return_value = {"error": "Unavailable"}
        for _ in range(2):
            with self.assertRaises(requests.RequestException):
                releases.get_product_release("acm", "acm-5.0", "5.0.0")
        self.assertEqual(status.call_count, 2)

    @patch.object(releases.requests, "get")
    def test_missing_release_file_is_empty_but_auth_failure_is_not(self, get):
        get.return_value = Mock(status_code=404)
        self.assertEqual(releases._build_data_yaml("acm-2.16", "releases.yml", optional=True), {})
        get.return_value = Mock(status_code=403)
        get.return_value.raise_for_status.side_effect = requests.HTTPError("Forbidden")
        with self.assertRaises(requests.HTTPError):
            releases._build_data_yaml("acm-2.16", "releases.yml", optional=True)

    @patch.object(gitlab, "_gitlab_get")
    def test_diff_pagination_and_deleted_files(self, get):
        get.side_effect = [[{"new_path": str(i)} for i in range(100)], [{"new_path": "deleted", "deleted_file": True}]]
        self.assertEqual(len(gitlab._get_mr_files("project", 1)), 100)
        self.assertIn("page=2", get.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
