

import threading
from datetime import datetime, timedelta

import plotly.express as px
from pandas import DataFrame, Series, Timedelta, concat, to_datetime

from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.impl.plotly.plotly_r_field import PlotlyRField

from ...core.service.base_service import BaseService
from .monitor import Monitor
from .monitor_dto import MonitorBetweenDateDTO


class MonitorService(BaseService):

    TICK_INTERVAL_SECONDS = 30   # 30 seconds
    TICK_INTERVAL_CLEANUP = 60 * 60 * 24  # 24 hours
    MONITORING_MAX_LINES = 86400  # 86400 = 1 log every 30 seconds for 1 month
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
        except Exception as err:
            Logger.error(f"Error while saving current monitor : {str(err)}")
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
        except Exception as err:
            Logger.error(f"Error while cleaning monitor data : {str(err)}")
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
                                           to_date_str: str,
                                           utc_num: int = 0) -> MonitorBetweenDateDTO:

        return cls.get_monitor_data_between_dates(
            DateHelper.from_iso_str(from_date_str),
            DateHelper.from_iso_str(to_date_str),
            utc_num
        )

    @classmethod
    def get_plotly_figure_dict(cls,
                               dataframe: DataFrame,
                               x: str,
                               y: list,
                               y_labs: dict = None) -> dict:
        # Create the plotly figure from the dataframe

        figure = px.line(dataframe, x=x, y=y, markers=True)
        if y_labs is None:
            y_labs = {y_: y_ for y_ in y}
        figure.for_each_trace(
            lambda t: t.update(
                name=y_labs[t.name],
                legendgroup=y_labs[t.name],
                hovertemplate=t.hovertemplate.replace(t.name, y_labs[t.name])
            )
        )
        figure.update_layout(
            {
                'title': '',
                'xaxis_title': '',
                'yaxis_title': '',
                'legend_title': '',
            }
        )

        # Convert the figure to a dict
        return PlotlyRField.figure_to_dict(figure)

    @classmethod
    def get_monitor_data_between_dates(cls,
                                       from_date: datetime,
                                       to_date: datetime,
                                       utc_number: int = 0) -> MonitorBetweenDateDTO:

        # convert date to string and add tick interval to be sure to have at least one tick
        from_date = from_date - timedelta(seconds=cls.TICK_INTERVAL_SECONDS)
        to_date = to_date + timedelta(seconds=cls.TICK_INTERVAL_SECONDS)

        monitors = list(Monitor.select().where(
            Monitor.created_at >= from_date,
            Monitor.created_at <= to_date).order_by(Monitor.created_at))

        if len(monitors) == 0:
            raise Exception("No monitor data found between the given dates")

        # vars transform the dto object to a dict
        df = DataFrame([vars(monitor.to_dto()) for monitor in monitors])

        if df.empty:
            return MonitorBetweenDateDTO(
                from_date=from_date,
                to_date=to_date,
                monitors=[],
                main_figure={},
                cpu_figure={},
                network_figure={}
            )

        # Add the utc number to the date if needed for plotly to display the correct date
        df['created_at'] = to_datetime(df['created_at'], utc=True)
        if utc_number != 0:
            df['created_at'] = df['created_at'] + Timedelta(hours=utc_number)

        # Create the main figure
        y_labels = {
            'cpu_percent': 'CPU',
            'disk_usage_percent': 'Disk Usage',
            'external_disk_usage_percent': 'External Disk Usage',
            'ram_usage_percent': 'RAM Usage',
            'swap_memory_percent': 'Swap Memory'
        }
        main_figure = cls.get_plotly_figure_dict(
            df, 'created_at',
            ['cpu_percent', 'disk_usage_percent', 'external_disk_usage_percent', 'ram_usage_percent',
             'swap_memory_percent'],
            y_labels)

        # Create the cpu figure
        df_cpu = df['data'].apply(lambda x: Series(x['all_cpu_percent']))
        df_cpu_columns = [f'CPU {i} (%)' for i in range(len(df_cpu.columns))]
        df_cpu.columns = df_cpu_columns
        df_cpu = concat([df['created_at'], df_cpu], axis=1)

        cpu_figure = cls.get_plotly_figure_dict(df_cpu, 'created_at', df_cpu_columns)

        # Create the network figure
        df_network = concat(
            [df['created_at'],
             df['net_io_bytes_recv'] / (1024 * 1024),
             df['net_io_bytes_sent'] / (1024 * 1024)],
            axis=1)
        df_network_columns = ['created_at', 'In (Mb)', 'Out (Mb)']
        df_network.columns = df_network_columns

        network_figure = cls.get_plotly_figure_dict(df_network, 'created_at', ['In (Mb)', 'Out (Mb)'])

        return MonitorBetweenDateDTO(
            from_date=from_date,
            to_date=to_date,
            monitors=[monitor.to_dto() for monitor in monitors],
            main_figure=main_figure,
            cpu_figure=cpu_figure,
            network_figure=network_figure
        )

    @classmethod
    def cleanup_old_monitor_data(cls):

        # Keep only last x records
        monitor: Monitor = Monitor.select().order_by(Monitor.created_at.desc()).offset(cls.MONITORING_MAX_LINES).first()

        if monitor is None:
            return
        # Delete all record older
        Monitor.delete().where(Monitor.created_at <= monitor.created_at).execute()
