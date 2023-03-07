# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import sys
from threading import Thread

from gws_core.central.central_service import CentralService
from gws_core.core.db.db_migration import DbMigrationService
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.logger import Logger
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_run_service import ExperimentRunService
from gws_core.impl.file.file_store import FileStore
from gws_core.impl.file.fs_node_model import FSNodeModel
from gws_core.impl.file.local_file_store import LocalFileStore
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.lab.monitor.monitor_service import MonitorService
from gws_core.project.project_service import ProjectService
from gws_core.resource.kv_store import KVStore
from gws_core.resource.resource_model import ResourceModel
from gws_core.user.user_dto import SpaceCentral

from ..brick.brick_service import BrickService
from ..core.exception.exceptions.unauthorized_exception import \
    UnauthorizedException
from ..core.model.base_model_service import BaseModelService
from ..core.utils.settings import Settings
from ..experiment.queue_service import QueueService
from ..impl.file.file_helper import FileHelper
from ..model.model_service import ModelService
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from ..user.user_service import UserService
from .system_status import SystemStatus


class SystemService:

    @classmethod
    def migrate_db(cls):
        DbMigrationService.migrate()

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
        LabConfigModel.save_current_config()

        # Init data folder
        cls.init_data_folder()

    @classmethod
    def init_data_folder(cls):
        settings = Settings.get_instance()
        FileHelper.create_dir_if_not_exist(settings.get_data_dir())
        FileHelper.create_dir_if_not_exist(settings.get_kv_store_base_dir())
        FileHelper.create_dir_if_not_exist(settings.get_file_store_dir())
        FileHelper.create_dir_if_not_exist(settings.get_brick_data_main_dir())

    @classmethod
    def init_queue_and_monitor(cls) -> None:
        MonitorService.init()
        QueueService.init(daemon=True)

    @classmethod
    def deinit_queue_and_monitor(cls) -> None:
        MonitorService.deinit()
        QueueService.deinit()

    @classmethod
    def create_all_tables(cls):
        """
        Create tables
        """

        BaseModelService.create_tables()

    @classmethod
    def drop_all_tables(cls):
        """
        Drops tables
        """
        settings: Settings = Settings.get_instance()
        if settings.is_prod:
            raise Exception('Cannot drop all table in prod env')

        BaseModelService.drop_tables()

    @classmethod
    def delete_temp_folder(cls):
        """
        Drops tables
        """
        settings: Settings = Settings.get_instance()

        if settings.is_prod:
            raise Exception('Cannot delete the temp folder in prod environment')
        FileHelper.delete_dir(settings.get_root_temp_dir())

    @classmethod
    def reset_dev_envionment(cls, check_user=True) -> None:
        settings: Settings = Settings.get_instance()

        if not settings.is_dev:
            raise UnauthorizedException('The reset method can only be called in dev environment')

        if check_user:
            user: User = CurrentUserService.get_and_check_current_user()

        if Experiment.table_exists():
            # Stop all running experiment
            ExperimentRunService.stop_all_running_experiment()

        cls.deinit_queue_and_monitor()

        cls.delete_temp_folder()
        cls.drop_all_tables()

        cls.init()
        cls.init_queue_and_monitor()

        if check_user:
            UserService.create_user_if_not_exists(user.to_user_data_dict())

    @classmethod
    def kill_process(cls) -> None:
        settings: Settings = Settings.get_instance()

        if not settings.is_dev:
            raise UnauthorizedException('The kill method can only be called in dev environment')

        sys.exit()

    @classmethod
    def register_lab_start(cls) -> None:
        """Method to call central after start to mark the lab as started in central
        """
        settings: Settings = Settings.get_instance()

        if settings.is_dev:
            return

        try:
            Logger.info('Registering lab start on central')

            result = CentralService.register_lab_start(LabConfigModel.get_current_config().to_json())

            if result:
                Logger.info('Lab start successfully registered on central')
            else:
                Logger.error('Error during lab start registration with central')

            cls.synchronize_with_central()
        except Exception as err:
            Logger.error(f"Error during lab start : {err}")
            Logger.log_exception_stack_trace(err)

    @classmethod
    def get_lab_info(cls) -> dict:
        settings = Settings.get_instance()
        return {
            "lab_name": settings.get_lab_name(),
            "front_version": settings.get_front_version(),
            "space": settings.get_space(),
            "id": settings.get_lab_id(),
        }

    @classmethod
    def save_space_async(cls, space_central: SpaceCentral) -> None:
        thread = Thread(target=cls._save_space, args=[space_central])
        thread.start()

    @classmethod
    def _save_space(cls, space_central: SpaceCentral) -> None:
        try:

            settings = Settings.get_instance()
            space = settings.get_space()

            # if no space were saved or one of its value was changed
            # update the space
            if space is None or space['id'] != space_central.id or \
                    space['name'] != space_central.name or space['domain'] != space_central.domain or \
                    space['photo'] != space_central.photo:
                settings.set_space({
                    "id": space_central.id,
                    'name': space_central.name,
                    'domain': space_central.domain,
                    'photo': space_central.photo,
                })
                settings.save()

        except Exception as err:
            Logger.error(f"Error while saving the space : {err}")
            Logger.log_exception_stack_trace(err)
            return None

    @classmethod
    def garbage_collector(cls) -> None:
        if len(ExperimentRunService.get_all_running_experiments()) > 0:
            raise BadRequestException('Cannot run the lab cleaning while there are running or waiting experiments')

        Logger.info('Starting the garbage collector')
        Logger.info('Deleting all the temp files')
        FileHelper.delete_dir_content(Settings.get_instance().get_root_temp_dir())

        Logger.info('Deleting all usunused resource kv stores')
        kv_store_dir = KVStore.get_base_dir()
        # loop through all the kv store files and folder

        for file_name in os.listdir(kv_store_dir):
            file_store_file_path = KVStore.get_full_file_path(file_name, with_extension=False)
            # if filename correspond to a ressource, don't delete it
            # check if filename is the resource id or is contained in the kv store path
            # (use contains for security to avoid deleting everything)
            if ResourceModel.get_or_none(
                    ResourceModel.kv_store_path.contains(file_name) or ResourceModel.id == file_name) is None:
                file_path = os.path.join(kv_store_dir, file_name)
                Logger.info(f'Deleting KVStore {file_path}')
                FileHelper.delete_node(file_path)

        Logger.info('Deleting all usunused resource files')
        file_store: LocalFileStore = FileStore.get_default_instance()
        for file_name in os.listdir(file_store.path):
            file_store_file_path = os.path.join(file_store.path, file_name)
            if FSNodeModel.get_or_none(FSNodeModel.path == file_store_file_path) is None:
                Logger.info(f'Deleting file {file_store_file_path}')
                FileHelper.delete_node(file_store_file_path)

        Logger.info('Ending the garbage collector')

    @classmethod
    def synchronize_with_central(cls, sync_users: bool = True, sync_projects: bool = True) -> None:
        if sync_users:
            UserService.synchronize_all_central_users()

        if sync_projects:
            ProjectService.synchronize_all_central_projects()
        Logger.info('Synchronization with central done')
