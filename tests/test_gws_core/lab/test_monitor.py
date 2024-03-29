
from unittest import TestCase

from gws_core.lab.monitor.monitor_service import MonitorService


# test_monitor
class TestMonitor(TestCase):

    def test_get_current_monitor(self):
        monitoring = MonitorService.get_current_monitor()

        self.assertNotEqual(monitoring.disk_total, 0.0)
        self.assertNotEqual(monitoring.disk_usage_used, 0.0)
        self.assertNotEqual(monitoring.disk_usage_free, 0.0)
        self.assertNotEqual(monitoring.disk_usage_percent, 0.0)

        self.assertNotEqual(monitoring.external_disk_total, 0.0)
        self.assertNotEqual(monitoring.external_disk_usage_used, 0.0)
        self.assertNotEqual(monitoring.external_disk_usage_free, 0.0)
        self.assertNotEqual(monitoring.external_disk_usage_percent, 0.0)

        self.assertNotEqual(monitoring.cpu_count, 0.0)
        self.assertNotEqual(monitoring.cpu_percent, 0.0)
        self.assertIsInstance(monitoring.get_all_cpu_percent, list)
        self.assertEqual(len(monitoring.get_all_cpu_percent), monitoring.cpu_count)

        self.assertIsNotNone(monitoring.swap_memory_total)
        self.assertIsNotNone(monitoring.swap_memory_used)
        self.assertIsNotNone(monitoring.swap_memory_free)
        self.assertIsNotNone(monitoring.swap_memory_percent)

        self.assertIsNotNone(monitoring.net_io_bytes_sent)
        self.assertIsNotNone(monitoring.net_io_bytes_recv)

        self.assertNotEqual(monitoring.ram_usage_total, 0.0)
        self.assertNotEqual(monitoring.ram_usage_used, 0.0)
        self.assertNotEqual(monitoring.ram_usage_free, 0.0)
        self.assertNotEqual(monitoring.ram_usage_percent, 0.0)
