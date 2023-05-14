import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fetchers import rpms_images_fetcher

class TestRpmsImagesFetcher(unittest.TestCase):
    def test_fetch_data(self):
        release = 'openshift-4.11'
        result = rpms_images_fetcher.fetch_data(release)

        # Check if the result is a list
        self.assertIsInstance(result, list)

        # Check if the list is not empty
        self.assertTrue(len(result) > 0)

        # Check if the result contains the correct release data
        found_release_data = False
        for item in result:
            if item['branch'] == release:
                found_release_data = True
                break
        print(result)
        self.assertTrue(found_release_data)

if __name__ == '__main__':
    unittest.main()