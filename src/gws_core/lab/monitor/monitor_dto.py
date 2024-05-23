

from datetime import datetime
from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO


class MonitorDTO(ModelDTO):
    cpu_count: float
    cpu_percent: float

    disk_total: float
    disk_usage_used: float
    disk_usage_free: float
    disk_usage_percent: float

    external_disk_total: float
    external_disk_usage_used: float
    external_disk_usage_free: float
    external_disk_usage_percent: float

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


class MonitorBetweenDateDTO(BaseModelDTO):

    from_date: datetime
    to_date: datetime
    monitors: List[MonitorDTO]
    main_figure: dict
    cpu_figure: dict
    network_figure: dict