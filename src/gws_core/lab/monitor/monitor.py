# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

import psutil
from peewee import FloatField

from gws_core.core.utils.settings import Settings

from ...core.model.model import Model

# ####################################################################
#
# Monitor
#
# ####################################################################


class Monitor(Model):
    """
    Lab Monitor class.

    This class provides functionalities for real-time monitoring the server status
    (e.g. cpu usage, disk usage, memory, network transactions)
    """

    # CPU
    cpu_count = FloatField()
    cpu_percent = FloatField()

    # Disk
    disk_total = FloatField()
    disk_usage_used = FloatField()
    disk_usage_free = FloatField()
    disk_usage_percent = FloatField()

    # External disk
    external_disk_total = FloatField(default=0)
    external_disk_usage_used = FloatField(default=0)
    external_disk_usage_free = FloatField(default=0)
    external_disk_usage_percent = FloatField(default=0)

    # Swap Memory
    swap_memory_total = FloatField()
    swap_memory_used = FloatField()
    swap_memory_free = FloatField()
    swap_memory_percent = FloatField()

    # Network
    net_io_bytes_sent = FloatField()
    net_io_bytes_recv = FloatField()

    # Ram
    ram_usage_total = FloatField(default=0)
    ram_usage_used = FloatField(default=0)
    ram_usage_free = FloatField(default=0)
    ram_usage_percent = FloatField(default=0)
    _table_name = 'gws_lab_monitor'

    @classmethod
    def get_last(cls):
        return Monitor.select().order_by(Monitor.created_at.desc()).get()

    @classmethod
    def get_current(cls):
        monitor = Monitor()

        # CPU
        monitor.cpu_count = psutil.cpu_count()
        monitor.cpu_percent = psutil.cpu_percent(interval=None)

        # All CPU
        monitor.data["all_cpu_percent"] = psutil.cpu_percent(
            interval=None, percpu=True)

        # Disk
        disk = psutil.disk_usage("/")
        monitor.disk_total = disk.total
        monitor.disk_usage_used = disk.used
        monitor.disk_usage_free = disk.free
        monitor.disk_usage_percent = disk.percent

        # External Disk
        disk = psutil.disk_usage(Settings.get_lab_folder())
        monitor.external_disk_total = disk.total
        monitor.external_disk_usage_used = disk.used
        monitor.external_disk_usage_free = disk.free
        monitor.external_disk_usage_percent = disk.percent

        # Network
        iobytes = psutil.net_io_counters()
        monitor.net_io_bytes_sent = iobytes.bytes_sent
        monitor.net_io_bytes_recv = iobytes.bytes_recv

        # Ram
        virtual_memory = psutil.virtual_memory()
        monitor.ram_usage_total = virtual_memory.total
        monitor.ram_usage_used = virtual_memory.used
        monitor.ram_usage_free = virtual_memory.free
        monitor.ram_usage_percent = virtual_memory.percent

        # Swap
        swap = psutil.swap_memory()
        monitor.swap_memory_total = swap.total
        monitor.swap_memory_used = swap.used
        monitor.swap_memory_free = swap.free
        monitor.swap_memory_percent = swap.percent

        return monitor

    @property
    def get_all_cpu_percent(self) -> List[float]:
        return self.data.get("all_cpu_percent", [])
