

import os
import sys
from threading import Thread
from typing import List

import plotly.express as px

from gws_core.core.db.db_migration import DbMigrationService
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.model.sys_proc import SysProc
from gws_core.core.utils.logger import Logger
from gws_core.folder.space_folder_service import SpaceFolderService
from gws_core.impl.file.file_store import FileStore
from gws_core.impl.file.fs_node_model import FSNodeModel
from gws_core.impl.file.local_file_store import LocalFileStore
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.lab.monitor.monitor_service import MonitorService
from gws_core.lab.system_dto import LabInfoDTO, LabSystemConfig
from gws_core.process.process_exception import ProcessRunException
from gws_core.process.process_types import ProcessErrorInfo
from gws_core.resource.kv_store import KVStore
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.scenario.scenario_run_service import ScenarioRunService
from gws_core.space.space_service import SpaceService
from gws_core.user.activity.activity_dto import (ActivityObjectType,
                                                 ActivityType)
from gws_core.user.activity.activity_service import ActivityService
from gws_core.user.user_dto import Space

from ..brick.brick_service import BrickService
from ..core.exception.exceptions.unauthorized_exception import \
    UnauthorizedException
from ..core.model.base_model_service import BaseModelService
from ..core.utils.settings import Settings
from ..impl.file.file_helper import FileHelper
from ..model.model_service import ModelService
from ..process.process_service import ProcessService
from ..scenario.queue_service import QueueService
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

        # Register lab start activity
        cls.register_start_activity()

        # Init plotly color, use the default plotly color
        # Force this init because it is overriden when importing streamlit
        px.defaults.color_discrete_sequence = px.colors.qualitative.Plotly

        if not Settings.get_instance().is_test:
            ProcessService.init_cron_thread_run_stats()

    @classmethod
    def register_start_activity(cls):
        sys_user = User.get_sysuser()
        ActivityService.add_with_catch(activity_type=ActivityType.LAB_START, object_type=ActivityObjectType.USER,
                                       object_id=sys_user.id, user=sys_user)

    @classmethod
    def init_data_folder(cls):
        settings = Settings.get_instance()
        FileHelper.create_dir_if_not_exist(settings.get_data_dir())
        FileHelper.create_dir_if_not_exist(settings.get_kv_store_base_dir())
        FileHelper.create_dir_if_not_exist(settings.get_file_store_dir())
        FileHelper.create_dir_if_not_exist(settings.get_brick_data_main_dir())

    @classmethod
    def init_queue_and_monitor(cls) -> None:
        cls._check_running_scenarios()
        MonitorService.init()
        QueueService.init(daemon=True)

    @classmethod
    def _check_running_scenarios(cls):
        # check for all running status scenario, if the process is still running
        # if not we consider that the scenario is not running

        try:
            CurrentUserService.set_current_user(User.get_sysuser())
            scenarios: List[Scenario] = list(Scenario.get_running_scenarios())

            for scenario in scenarios:
                if scenario.get_process_status() != ScenarioStatus.RUNNING:
                    Logger.info(f"Marking scenario {scenario.id} as stopped because the process is not running")
                    running_process = scenario.protocol_model.get_running_task()

                    error_text = "The lab was stopped while the scenario was running. It killed the scenario's process. Marking the scenario as stopped."
                    if running_process is not None:
                        running_process.mark_as_error_and_parent(ProcessRunException.from_exception(
                            process_model=running_process, exception=Exception(error_text),
                            error_prefix="Lab init"))
                    else:
                        scenario.mark_as_error(ProcessErrorInfo(
                            detail="The lab was stopped while the scenario was running. It killed the scenario's process. Marking the scenario as stopped.",
                            unique_code="LAB_STOPPED_WHILE_RUNNING", context=None, instance_id=None))
        except Exception as err:
            Logger.error(
                f'[SystemService] Error while checking running scenarios: {err}')
            Logger.log_exception_stack_trace(err)
        finally:
            CurrentUserService.set_current_user(None)

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
        if Settings.is_prod_mode():
            raise Exception('Cannot drop all table in prod env')

        BaseModelService.drop_tables()

    @classmethod
    def delete_temp_folder(cls):
        """
        Drops tables
        """
        settings: Settings = Settings.get_instance()

        if settings.is_prod_mode():
            raise Exception(
                'Cannot delete the temp folder in prod environment')
        FileHelper.delete_dir(settings.get_root_temp_dir())

    @classmethod
    def reset_dev_envionment(cls, check_user=True) -> None:

        if not Settings.is_dev_mode():
            raise UnauthorizedException(
                'The reset method can only be called in dev environment')

        if check_user:
            user: User = CurrentUserService.get_and_check_current_user()

        Logger.info('Resetting the dev environment')

        try:
            if Scenario.table_exists():
                # Stop all running scenario
                ScenarioRunService.stop_all_running_scenario()
        except Exception as err:
            Logger.error(
                f"[SystemService] Error while stopping all running scenarios: {err}, continue...")
            Logger.log_exception_stack_trace(err)

        cls.deinit_queue_and_monitor()

        cls.delete_temp_folder()
        cls.drop_all_tables()
        # clean kvstore
        FileHelper.delete_node(Settings.get_instance().get_kv_store_base_dir())

        cls.init()
        cls.init_queue_and_monitor()

        if check_user:
            UserService.create_or_update_user_dto(user.to_full_dto())

        Logger.info('Dev environment resetted')

    @classmethod
    def kill_dev_environment(cls) -> None:
        if not Settings.is_dev_mode():
            raise UnauthorizedException(
                'The kill method can only be called in dev environment')

        Logger.info('Killing the dev environment')

        # kill current process and all its children
        sys_proc = SysProc.from_pid(os.getpid())
        sys_proc.kill_with_children()

    @classmethod
    def register_lab_start(cls) -> None:
        """Method to call space after start to mark the lab as started in space
        """

        if Settings.is_dev_mode():
            return

        try:
            Logger.info('Registering lab start on space')

            result = SpaceService.register_lab_start(
                LabConfigModel.get_current_config().to_dto())

            if result:
                Logger.info('Lab start successfully registered on space')
            else:
                Logger.error('Error during lab start registration with space')

            cls.synchronize_with_space()
        except Exception as err:
            Logger.error(f"Error during lab start : {err}")
            Logger.log_exception_stack_trace(err)

    @classmethod
    def get_lab_info(cls) -> LabInfoDTO:
        settings = Settings.get_instance()
        return LabInfoDTO(
            lab_name=settings.get_lab_name(),
            front_version=settings.get_front_version(),
            space=settings.get_space(),
            id=settings.get_lab_id(),
        )

    @classmethod
    def save_space_async(cls, space: Space) -> None:
        thread = Thread(target=cls._save_space, args=[space])
        thread.start()

    @classmethod
    def _save_space(cls, space: Space) -> None:
        try:

            settings = Settings.get_instance()
            db_space_dict = settings.get_space()

            # if no space were saved or one of its value was changed
            # update the space
            if db_space_dict is None or db_space_dict['id'] != space.id or \
                    db_space_dict['name'] != space.name or db_space_dict['domain'] != space.domain or \
                    db_space_dict['photo'] != space.photo:
                settings.set_space({
                    "id": space.id,
                    'name': space.name,
                    'domain': space.domain,
                    'photo': space.photo,
                })
                settings.save()

        except Exception as err:
            Logger.error(f"Error while saving the space : {err}")
            Logger.log_exception_stack_trace(err)
            return None

    @classmethod
    def garbage_collector(cls) -> None:
        if len(ScenarioRunService.get_all_running_scenarios()) > 0:
            raise BadRequestException(
                'Cannot run the lab cleaning while there are running or waiting scenarios')

        Logger.info('Starting the garbage collector')

        temp_root_dir = Settings.get_instance().get_root_temp_dir()
        if FileHelper.exists_on_os(temp_root_dir):
            Logger.info('Deleting all the temp files')
            FileHelper.delete_dir_content(temp_root_dir)

        # loop through all the kv store files and folder
        kv_store_dir = KVStore.get_base_dir()
        if FileHelper.exists_on_os(kv_store_dir):
            Logger.info('Deleting all usunused resource kv stores')
            for file_name in os.listdir(kv_store_dir):
                file_store_file_path = KVStore.get_full_file_path(
                    file_name, with_extension=False)
                # if filename correspond to a ressource, don't delete it
                # check if filename is the resource id or is contained in the kv store path
                # (use contains for security to avoid deleting everything)
                if ResourceModel.get_or_none(
                    (ResourceModel.kv_store_path.contains(file_name)) |
                        (ResourceModel.id == file_name)) is None:
                    file_path = os.path.join(kv_store_dir, file_name)
                    Logger.info(f'Deleting KVStore {file_path}')
                    FileHelper.delete_node(file_path)

        file_store: LocalFileStore = FileStore.get_default_instance()
        if FileHelper.exists_on_os(file_store.path):
            Logger.info('Deleting all usunused resource files')
            for file_name in os.listdir(file_store.path):
                file_store_file_path = os.path.join(file_store.path, file_name)
                if FSNodeModel.get_or_none(FSNodeModel.path == file_store_file_path) is None:
                    Logger.info(f'Deleting file {file_store_file_path}')
                    FileHelper.delete_node(file_store_file_path)

        Logger.info('Ending the garbage collector')

    @classmethod
    def synchronize_with_space(cls, sync_users: bool = True, sync_folders: bool = True) -> None:
        if sync_users:
            UserService.synchronize_all_space_users()

        if sync_folders:
            SpaceFolderService.synchronize_all_space_folders()
        Logger.info('Synchronization with space done')

    @classmethod
    def get_system_config(cls) -> LabSystemConfig:
        return LabSystemConfig(
            python_version=sys.version,
            pip_packages=Settings.get_instance().get_all_pip_packages()
        )
