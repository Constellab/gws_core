# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import sys

from gws_core.tag.tag_service import TagService

from ..brick.brick_service import BrickService
from ..core.exception.exceptions.unauthorized_exception import \
    UnauthorizedException
from ..core.utils.settings import Settings
from ..experiment.experiment_service import ExperimentService
from ..experiment.queue_service import QueueService
from ..impl.file.file_helper import FileHelper
from ..model.model_service import ModelService
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from ..user.user_service import UserService
from .monitor import Monitor
from .system_status import SystemStatus


class SystemService:

    @classmethod
    def init(cls):
        """
        Init method init all the api.
         - create all the table if not exists
         - register the processes and resources
         - create the sysuser if not exists
        """
        cls.create_all_tables()
        ModelService.register_all_processes_and_resources()
        UserService.create_sysuser()
        SystemStatus.app_is_initialized = True

        BrickService.init()
        TagService.init_default_tags()

    @classmethod
    def init_queue_and_monitor(cls) -> None:
        Monitor.init(daemon=True)
        QueueService.init(daemon=True)

    @classmethod
    def deinit_queue_and_monitor(cls) -> None:
        Monitor.deinit()
        QueueService.deinit()

    @classmethod
    def create_all_tables(cls):
        """
        Create tables
        """

        ModelService.create_tables()

    @classmethod
    def drop_all_tables(cls):
        """
        Drops tables
        """
        settings: Settings = Settings.retrieve()
        if settings.is_prod:
            raise Exception('Cannot drop all table in prod env')

        ModelService.drop_tables()

    @classmethod
    def delete_temp_folder(cls):
        """
        Drops tables
        """
        settings: Settings = Settings.retrieve()

        if settings.is_prod:
            raise Exception('Cannot delete the temp folder in prod environment')
        FileHelper.delete_dir(settings.get_root_temp_dir())

    @classmethod
    def reset_dev_envionment(cls) -> None:
        settings: Settings = Settings.retrieve()

        if not settings.is_dev:
            raise UnauthorizedException('The reset method can only be called in dev environment')

        user: User = CurrentUserService.get_and_check_current_user()

        # Stop all running experiment
        ExperimentService.stop_all_running_experiment()

        cls.deinit_queue_and_monitor()

        cls.delete_temp_folder()
        cls.drop_all_tables()

        cls.init()
        cls.init_queue_and_monitor()

        UserService.create_user_if_not_exists(user.to_user_data_dict())

    @classmethod
    def kill_process(cls) -> None:
        settings: Settings = Settings.retrieve()

        if not settings.is_dev:
            raise UnauthorizedException('The kill method can only be called in dev environment')

        sys.exit()
