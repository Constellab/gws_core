# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import threading
from datetime import datetime, timedelta

from gws_core.core.utils.date_helper import DateHelper

from ...core.classes.paginator import Paginator
from ...core.service.base_service import BaseService
from .monitor import Monitor
from .monitor_dto import MonitorBetweenDateDTO


class MonitorService(BaseService):

    TICK_INTERVAL_SECONDS = 30   # 30 seconds
    TICK_INTERVAL_CLEANUP = 60 * 60 * 24  # 24 hours
    MONITORING_MAX_AGE = 60 * 60 * 24 * 30  # 30 days, clear monitoring data older than 30 days
    _is_initialized: bool = False

    @classmethod
    def init(cls):
        if not cls._is_initialized:
            cls._is_initialized = True
            cls._system_monitor_tick()
            cls._system_monitor_cleanup()

    @classmethod
    def _system_monitor_tick(cls):
        if not MonitorService._is_initialized:
            return
        try:
            MonitorService.save_current_monitor()
        finally:
            thread = threading.Timer(
                cls.TICK_INTERVAL_SECONDS, cls._system_monitor_tick)
            thread.daemon = True
            thread.start()

    @classmethod
    def _system_monitor_cleanup(cls):
        if not MonitorService._is_initialized:
            return
        try:
            MonitorService.cleanup_old_monitor_data()
        finally:
            thread = threading.Timer(
                cls.TICK_INTERVAL_CLEANUP, cls._system_monitor_cleanup)
            thread.daemon = True
            thread.start()

    @classmethod
    def deinit(cls):
        cls._is_initialized = False

    @classmethod
    def save_current_monitor(cls) -> Monitor:
        monitor = cls.get_current_monitor()
        return monitor.save()

    @classmethod
    def get_current_monitor(cls) -> Monitor:
        return Monitor.get_current()

    @classmethod
    def get_monitor_data_between_dates_str(cls,
                                           from_date_str: str,
                                           to_date_str: str) -> MonitorBetweenDateDTO:

        return cls.get_monitor_data_between_dates(
            DateHelper.from_iso_str(from_date_str),
            DateHelper.from_iso_str(to_date_str)
        )

    @classmethod
    def get_monitor_data_between_dates(cls,
                                       from_date: datetime,
                                       to_date: datetime) -> MonitorBetweenDateDTO:

        # convert date to string and add tick interval to be sure to have at least one tick
        from_date = from_date - timedelta(seconds=cls.TICK_INTERVAL_SECONDS)
        to_date = to_date + timedelta(seconds=cls.TICK_INTERVAL_SECONDS)

        monitors = list(Monitor.select().where(
            Monitor.created_at >= from_date,
            Monitor.created_at <= to_date).order_by(Monitor.created_at))

        return MonitorBetweenDateDTO(
            from_date=from_date,
            to_date=to_date,
            monitors=monitors
        )

    @classmethod
    def cleanup_old_monitor_data(cls):
        date = DateHelper.now_utc() - timedelta(seconds=cls.MONITORING_MAX_AGE)

        Monitor.delete().where(Monitor.created_at < date).execute()