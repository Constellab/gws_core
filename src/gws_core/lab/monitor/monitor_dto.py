from datetime import datetime
from typing import Dict, Optional

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO


class MonitorDTO(ModelDTO):
    cpu_count: float
    cpu_percent: float

    disk_total: float
    disk_usage_used: float
    disk_usage_free: float
    disk_usage_percent: float

    swap_memory_total: float
    swap_memory_used: float
    swap_memory_free: float
    swap_memory_percent: float

    net_io_bytes_sent: float
    net_io_bytes_recv: float

    ram_usage_total: float
    ram_usage_used: float
    ram_usage_free: float
    ram_usage_percent: float

    gpu_enabled: bool
    gpu_percent: Optional[float]
    gpu_temperature: Optional[float]
    gpu_memory_total: Optional[float]
    gpu_memory_used: Optional[float]
    gpu_memory_free: Optional[float]
    gpu_memory_percent: Optional[float]

    data: dict


class MonitorFreeDiskDTO(BaseModelDTO):
    required_disk_free_space: float
    disk_usage_free: float

    def has_enough_space_for_file(self, file_size: float) -> bool:
        remaining_space_after_file = self.get_remaining_space_after_file(file_size)

        return remaining_space_after_file > self.required_disk_free_space

    def get_remaining_space_after_file(self, file_size: float) -> float:
        return self.disk_usage_free - file_size


class CurrentMonitorDTO(BaseModelDTO):
    monitor: MonitorDTO
    free_disk: MonitorFreeDiskDTO


class MonitorBetweenDateGraphicsDTO(BaseModelDTO):
    from_date: datetime
    to_date: datetime
    main_figure: Dict
    cpu_figure: Dict
    network_figure: Dict
    gpu_enabled: bool
    gpu_figure: Optional[Dict]


class GetMonitorTimezoneDTO(BaseModelDTO):
    timezone_number: Optional[float]


class GetMonitorRequestDTO(GetMonitorTimezoneDTO):
    from_date: Optional[str]
    to_date: Optional[str]
