

from multiprocessing import Process
from time import sleep

import requests

from gws_core.app import App
from gws_core.core.utils.settings import Settings
from gws_core.credentials.credentials import Credentials
from gws_core.credentials.credentials_service import CredentialsService
from gws_core.credentials.credentials_type import (CredentialsDataLab,
                                                   CredentialsType,
                                                   SaveCredentialsDTO)
from gws_core.folder.space_folder import SpaceFolder
from gws_core.impl.robot.robot_resource import Robot
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.user.user import User
from gws_core.user.user_group import UserGroup

from ..core.console.console import Console


class GTest(Console):
    """
    GTest class.

    Provides functionalities to initilize unit testing environments
    """

    @classmethod
    def create_default_folder(cls) -> SpaceFolder:
        """
        Get a default folder
        """
        return SpaceFolder(title="Default folder",
                           description="Folder description").save()

    @classmethod
    def get_test_user(cls) -> User:
        """
        Get a default User
        """
        return User(email="test@gencovery.com",
                    first_name="Test",
                    last_name="User",
                    group=UserGroup.USER)

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
        return CredentialsService.create(SaveCredentialsDTO(name="test", type=CredentialsType.LAB,
                                                            data=lab_credentials.to_json_dict()))


class TestStartUvicornApp():
    """ Context to support with statement start the uvicorn api server in tests.
    It automatically starts the server when entering the context and stops it when exiting.
    """

    process: Process = None

    def enter(self):
        self.__enter__()

    def exit(self, exc_type, exc_value, traceback):
        self.__exit__(exc_type, exc_value, traceback)

    def __enter__(self):
        # Registrer the lab start. Use a new thread to prevent blocking the start
        self.process = Process(target=App.start_uvicorn_app)
        self.process.start()

        health_check_route = f"{Settings.get_lab_api_url()}/{Settings.core_api_route_path()}/health-check"

        # Wait for the server to start
        i = 0
        while i < 10:
            try:
                response = requests.get(health_check_route, timeout=1)
                if response.status_code == 200:
                    return
            except Exception:
                pass
            i += 1
            sleep(1)

        raise Exception("Server not started")

    def __exit__(self, exc_type, exc_value, traceback):
        # force kill the thread
        self.process.terminate()

        # raise the exception if exists
        if exc_value:
            raise exc_value
