import os
from abc import abstractmethod
from collections.abc import Callable

from gws_core.apps.app_dto import AppType
from gws_core.brick.brick_service import BrickService
from gws_core.core.model.base_typing import BaseTyping
from gws_core.core.utils.utils import Utils
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.model.typing_register_decorator import register_gws_typing_class
from gws_core.model.typing_style import TypingStyle


class AppConfig(BaseTyping):
    """Extends this class to create an app.

    This class defines what code to use to run the app and in which virtual environment if needed.

    The sub class must implement the get_folder_path method to return the path of the folder containing the app

    """

    @abstractmethod
    def get_app_folder_path(self) -> str:
        """
        :return: path of the folder containing the app code
        :rtype: str
        """

    def get_shell_proxy(self) -> ShellProxy:
        """Override this method to return a env shell proxy if your app
        needs to run in a virtual environment.

        :return: _description_
        :rtype: ShellProxy
        """
        return ShellProxy()

    def get_app_folder_from_relative_path(self, current_file: str, app_folder_name: str) -> str:
        """Method to get the app folder from a relative path.

        :param current_file: path of the current file (__file__)
        :type current_file: str
        :param folder_name: name of the app folder
        :type folder_name: str
        :return: _description_
        :rtype: str
        """
        return os.path.join(os.path.abspath(os.path.dirname(current_file)), app_folder_name)


def app_decorator(
    unique_name: str, app_type: AppType, human_name: str = "", short_description: str = ""
) -> Callable:
    """ Decorator to declare a app class configuration.

    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type unique_name: str
    :param app_type: type of the app_type
    :type app_type: AppType
    :param human_name: optional name that will be used in the interface when viewing the tasks.
                        If not defined, the unique_name will be used
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the tasks. Must not be longer than 255 caracters.
    :type short_description: str, optional

    """

    def decorator(task_class: type[AppConfig]):
        _decorate_app(
            task_class,
            app_type=app_type,
            unique_name=unique_name,
            human_name=human_name,
            short_description=short_description,
        )

        return task_class

    return decorator


def _decorate_app(
    app_class: type[AppConfig],
    app_type: AppType,
    unique_name: str,
    human_name: str = "",
    short_description: str = "",
):
    """Method to decorate a task"""
    if not Utils.issubclass(app_class, AppConfig):
        BrickService.log_brick_error(
            app_class,
            f"The app_decorator is used on the class: {app_class.__name__} and this class is not a sub class of App",
        )
        return

    if not isinstance(app_type, AppType):
        BrickService.log_brick_error(
            app_class, f"The app_type: {app_type} is not a instance of AppType"
        )
        return

    register_gws_typing_class(
        object_class=app_class,
        object_type="APP",
        unique_name=unique_name,
        object_sub_type=app_type.value,
        human_name=human_name,
        short_description=short_description,
        hide=True,
        style=TypingStyle.default_task(),
        deprecated=None,
    )
