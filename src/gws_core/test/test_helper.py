import shutil

from gws_core.core.model.base_model_service import BaseModelService
from gws_core.core.utils.settings import Settings
from gws_core.credentials.credentials import Credentials
from gws_core.credentials.credentials_service import CredentialsService
from gws_core.credentials.credentials_type import (
    CredentialsDataLab,
    CredentialsType,
    SaveCredentialsDTO,
)
from gws_core.folder.space_folder import SpaceFolder
from gws_core.impl.robot.robot_resource import Robot
from gws_core.lab.system_service import SystemService
from gws_core.lab.system_status import SystemStatus
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.user.authorization_service import AuthorizationService
from gws_core.user.user import User
from gws_core.user.user_group import UserGroup


class TestHelper:
    """
    Provides functionalities to initilize unit testing environments
    """

    user: User = None

    @classmethod
    def init_complete(cls):
        """
        This function initializes objects for unit testing
        """

        if not Settings.is_dev_mode():
            raise Exception("The unit tests can only be initialized in dev mode")

        SystemService.init()

        user = User.get_and_check_sysuser()

        # refresh user information from DB
        AuthorizationService.authenticate_user(user_id=user.id)

        cls.user = user

    @classmethod
    def init(cls):
        """
        This function initializes objects for unit testing
        """

        if not Settings.is_dev_mode():
            raise Exception("The unit tests can only be initialized in dev mode")

        SystemService.init_data_folder()
        SystemStatus.app_is_initialized = True

    @classmethod
    def drop_tables(cls):
        """
        Drops tables
        """

        BaseModelService.drop_tables()

    @classmethod
    def delete_data_and_temp_folder(cls):
        """
        Drops tables
        """
        settings: Settings = Settings.get_instance()

        if not settings.is_test:
            raise Exception("Can only delete the data and temp folder in test env")
        shutil.rmtree(path=settings.get_data_dir(), ignore_errors=True)
        SystemService.delete_temp_folder()

    @classmethod
    def create_default_folder(cls) -> SpaceFolder:
        """
        Get a default folder
        """
        return SpaceFolder(title="Default folder", description="Folder description").save()

    @classmethod
    def get_test_user(cls) -> User:
        """
        Get a default User
        """
        return User(
            email="test@gencovery.com", first_name="Test", last_name="User", group=UserGroup.USER
        )

    @classmethod
    def save_robot_resource(cls) -> ResourceModel:
        """
        Save a robot resource
        """
        robot = Robot.empty()
        return ResourceModel.save_from_resource(robot, origin=ResourceOrigin.UPLOADED)

    @classmethod
    def create_lab_credentials(cls) -> Credentials:
        """
        Create lab credentials that reference itself
        """
        lab_credentials = CredentialsDataLab(lab_domain="http://localhost", api_key="test")
        return CredentialsService.create(
            SaveCredentialsDTO(
                name="test", type=CredentialsType.LAB, data=lab_credentials.to_json_dict()
            )
        )
