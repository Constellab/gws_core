# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from datetime import datetime
from typing import List

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
    gpu_percent: float
    gpu_temperature: float
    gpu_memory_total: float
    gpu_memory_used: float
    gpu_memory_free: float
    gpu_memory_percent: float


class MonitorBetweenDateDTO(BaseModelDTO):

    from_date: datetime
    to_date: datetime
    monitors: List[MonitorDTO]
