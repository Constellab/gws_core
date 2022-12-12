# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from datetime import datetime
from typing import List

from .monitor import Monitor


class MonitorBetweenDateDTO():

    from_date: datetime
    to_date: datetime
    monitors: List[Monitor]

    def __init__(self, from_date: datetime, to_date: datetime, monitors: List[Monitor]):
        self.from_date = from_date
        self.to_date = to_date
        self.monitors = monitors

    def to_json(self):
        return {
            "from_date": self.from_date,
            "to_date": self.to_date,
            "monitors": [monitor.to_json() for monitor in self.monitors]
        }
