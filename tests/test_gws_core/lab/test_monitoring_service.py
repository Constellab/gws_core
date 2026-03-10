from gws_core.lab.monitor.monitor_service import MonitorService
from gws_core.test.base_test_case import BaseTestCase


# test_monitoring_service
class TestMonitoringService(BaseTestCase):
    def test_get_folder_sizes(self):
        result = MonitorService.get_folder_sizes()

        # Check the result structure
        self.assertIsNotNone(result)
        self.assertIsInstance(result.folders, list)
        self.assertGreater(len(result.folders), 0)
        self.assertIsInstance(result.total_size, int)
        self.assertGreaterEqual(result.total_size, 0)

        # Check each folder DTO has the expected fields
        for folder in result.folders:
            self.assertIsNotNone(folder.name)
            self.assertIsNotNone(folder.pretty_name)
            self.assertIsNotNone(folder.path)
            # If no error, size should be a positive int
            if folder.error is None:
                self.assertIsNotNone(folder.size)
                self.assertGreaterEqual(folder.size, 0)

        # Check that known folders are present (user and bricks should always exist)
        folder_names = [f.name for f in result.folders]
        self.assertIn("user", folder_names)

        # Check that total_size equals the sum of all valid folder sizes
        expected_total = sum(f.size for f in result.folders if f.size is not None)
        self.assertEqual(result.total_size, expected_total)
