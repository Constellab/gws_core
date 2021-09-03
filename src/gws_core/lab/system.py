# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import threading

import psutil
from peewee import FloatField

from ..core.model.model import Model
from ..model.typing_register_decorator import typing_registrator

TICK_INTERVAL_SECONDS = 60*5   # 5 min


def _system_monitor_tick(daemon):
    try:
        Monitor._tick()
    finally:
        if Monitor._is_init:
            thread = threading.Timer(
                TICK_INTERVAL_SECONDS, _system_monitor_tick, [daemon])
            thread.daemon = daemon
            thread.start()

# ####################################################################
#
# Monitor
#
# ####################################################################


@typing_registrator(unique_name="Monitor", object_type="GWS_CORE", hide=True)
class Monitor(Model):
    """
    Lab Monitor class.

    This class provides functionalities for real-time monitoring the server status
    (e.g. cpu usage, disk usage, memory, network transactions)
    """
    cpu_count = FloatField()
    cpu_percent = FloatField(index=True)
    disk_total = FloatField()
    disk_usage_used = FloatField(index=True)
    disk_usage_free = FloatField(index=True)
    disk_usage_percent = FloatField(index=True)
    swap_memory_total = FloatField(index=True)
    swap_memory_used = FloatField(index=True)
    swap_memory_free = FloatField(index=True)
    swap_memory_percent = FloatField(index=True)
    net_io_bytes_sent = FloatField(index=True)
    net_io_bytes_recv = FloatField(index=True)
    _table_name = 'gws_lab_monitor'
    _is_init = False

    @classmethod
    def init(cls, daemon=False):
        if not cls._is_init:
            cls._is_init = True
            _system_monitor_tick(daemon)

    @classmethod
    def deinit(cls):
        cls._is_init = False

    @classmethod
    def get_last(cls):
        return Monitor.select().order_by(Monitor.id.desc()).get()

    @classmethod
    def _tick(cls):
        try:
            monitor = Monitor()
            disk = psutil.disk_usage("/")
            swap = psutil.swap_memory()
            iobytes = psutil.net_io_counters()
            monitor.cpu_count = psutil.cpu_count()
            monitor.cpu_percent = psutil.cpu_percent(interval=None)
            monitor.data["all_cpu_percent"] = psutil.cpu_percent(
                interval=None, percpu=True)
            monitor.disk_total = disk.total
            monitor.disk_usage_used = disk.used
            monitor.disk_usage_free = disk.free
            monitor.disk_usage_percent = disk.percent
            monitor.swap_memory_total = swap.total
            monitor.swap_memory_used = swap.used
            monitor.swap_memory_free = swap.free
            monitor.swap_memory_percent = swap.percent
            monitor.net_io_bytes_sent = iobytes.bytes_sent
            monitor.net_io_bytes_recv = iobytes.bytes_recv
            monitor.save()
        except:
            pass
