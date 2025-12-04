import random
from datetime import datetime

from gws_core.lab.monitor.monitor import Monitor
from gws_core.lab.monitor.monitor_service import MonitorService
from gws_core.test.base_test_case import BaseTestCase


# test_monitor
class TestMonitor(BaseTestCase):
    def test_get_current_monitor(self):
        monitoring = Monitor.get_current()

        self.assertNotEqual(monitoring.disk_total, 0.0)
        self.assertNotEqual(monitoring.disk_usage_used, 0.0)
        self.assertNotEqual(monitoring.disk_usage_free, 0.0)
        self.assertNotEqual(monitoring.disk_usage_percent, 0.0)

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

    def test_get_monitor_between_date(self):
        # date range
        from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        to_date = datetime.now()

        monitor_time = []

        n = 10
        for i in range(n):
            # append random time between from_date and to_date
            monitor_time.append(from_date + (to_date - from_date) * random.random())

        # Create random monitors data between from_date and to_date
        for time in monitor_time:
            m = Monitor(
                cpu_count=3,
                cpu_percent=random.randint(0, 100),
                disk_total=random.randint(0, 100),
                disk_usage_used=random.randint(0, 100),
                disk_usage_free=random.randint(0, 100),
                disk_usage_percent=random.randint(0, 100),
                net_io_bytes_sent=random.randint(0, 100),
                net_io_bytes_recv=random.randint(0, 100),
                ram_usage_total=random.randint(0, 100),
                ram_usage_used=random.randint(0, 100),
                ram_usage_free=random.randint(0, 100),
                ram_usage_percent=random.randint(0, 100),
                swap_memory_total=random.randint(0, 100),
                swap_memory_used=random.randint(0, 100),
                swap_memory_free=random.randint(0, 100),
                swap_memory_percent=random.randint(0, 100),
                data={"all_cpu_percent": [random.randint(0, 100) for _ in range(3)]},
                created_at=time,
            )
            m.save()

        # Get monitor data between from_date and to_date
        monitor_between_date = MonitorService.get_monitor_data_graphics_between_dates(
            from_date=from_date, to_date=to_date
        )

        self.assertTrue(monitor_between_date.from_date <= monitor_between_date.to_date)
        self.assertIsNotNone(monitor_between_date.main_figure)
        self.assertIsNotNone(monitor_between_date.cpu_figure)
        self.assertIsNotNone(monitor_between_date.network_figure)
        self.assertIsNotNone(monitor_between_date.gpu_figure)
