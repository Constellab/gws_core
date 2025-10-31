

import subprocess
from typing import Any, Dict, List

import psutil
from gws_core.core.model.db_field import JSONField
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.lab.monitor.monitor_dto import MonitorDTO
from peewee import FloatField

from ...core.model.model import Model


class GpuInfo(BaseModelDTO):
    percent: float
    temperature: float
    memory_total: float
    memory_used: float
    memory_free: float
    memory_percent: float


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

    # Gpu
    gpu_percent = FloatField(default=0)
    gpu_temperature = FloatField(default=0)
    gpu_memory_total = FloatField(default=0)
    gpu_memory_used = FloatField(default=0)
    gpu_memory_free = FloatField(default=0)
    gpu_memory_percent = FloatField(default=0)

    data: Dict[str, Any] = JSONField(null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_saved() and not self.data:
            self.data = {}

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
        disk = cls.get_current_disk_usage()
        monitor.disk_total = disk.total
        monitor.disk_usage_used = disk.used
        monitor.disk_usage_free = disk.free
        monitor.disk_usage_percent = disk.percent

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

        # Gpu
        if Settings.gpu_is_available():
            gpu_info = cls.get_gpu_info()
            if gpu_info:
                monitor.gpu_percent = gpu_info.percent
                monitor.gpu_temperature = gpu_info.temperature
                monitor.gpu_memory_total = gpu_info.memory_total
                monitor.gpu_memory_used = gpu_info.memory_used
                monitor.gpu_memory_free = gpu_info.memory_free
                monitor.gpu_memory_percent = gpu_info.memory_percent

        return monitor

    @classmethod
    def get_current_disk_usage(cls):
        disk_path = Settings.get_monitor_disk_path()
        return psutil.disk_usage(disk_path)

    @classmethod
    def get_gpu_info(cls) -> GpuInfo:
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu,memory.total,memory.used,memory.free',
                 '--format=csv,noheader,nounits'], stdout=subprocess.PIPE, check=True)

            gpu_info = result.stdout.decode('UTF-8').split('\n')[0].split(', ')

            memory_used = float(gpu_info[3]) * 1024 * 1024 * 1024
            memory_free = float(gpu_info[4]) * 1024 * 1024 * 1024
            memory_total = float(gpu_info[2]) * 1024 * 1024 * 1024
            return GpuInfo(
                percent=float(gpu_info[0]),
                temperature=float(gpu_info[1]),
                memory_total=memory_total,
                memory_used=memory_used,
                memory_free=memory_free,
                memory_percent=memory_used / memory_total * 100
            )
        except Exception as err:
            Logger.debug(f"Error while getting gpu info from nvidia-smi : {err}")
            return None

    @property
    def get_all_cpu_percent(self) -> List[float]:
        return self.data.get("all_cpu_percent", [])

    def to_dto(self) -> MonitorDTO:
        return MonitorDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            cpu_count=self.cpu_count,
            cpu_percent=self.cpu_percent,
            disk_total=self.disk_total,
            disk_usage_used=self.disk_usage_used,
            disk_usage_free=self.disk_usage_free,
            disk_usage_percent=self.disk_usage_percent,
            swap_memory_total=self.swap_memory_total,
            swap_memory_used=self.swap_memory_used,
            swap_memory_free=self.swap_memory_free,
            swap_memory_percent=self.swap_memory_percent,
            net_io_bytes_sent=self.net_io_bytes_sent,
            net_io_bytes_recv=self.net_io_bytes_recv,
            ram_usage_total=self.ram_usage_total,
            ram_usage_used=self.ram_usage_used,
            ram_usage_free=self.ram_usage_free,
            ram_usage_percent=self.ram_usage_percent,
            gpu_enabled=Settings.gpu_is_available(),
            gpu_percent=self.gpu_percent,
            gpu_temperature=self.gpu_temperature,
            gpu_memory_total=self.gpu_memory_total,
            gpu_memory_used=self.gpu_memory_used,
            gpu_memory_free=self.gpu_memory_free,
            gpu_memory_percent=self.gpu_memory_percent,
            data=self.data
        )

    class Meta:
        table_name = 'gws_lab_monitor'
        is_table = True
