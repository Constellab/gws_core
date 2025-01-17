

from abc import abstractmethod
from enum import Enum
from typing import Callable, Type

from gws_core.brick.brick_service import BrickService
from gws_core.core.model.base_typing import BaseTyping
from gws_core.core.utils.utils import Utils
from gws_core.model.typing_register_decorator import register_gws_typing_class
from gws_core.model.typing_style import TypingStyle
from gws_core.streamlit.streamlit_app import StreamlitAppType


class DashboardType(Enum):
    STREAMLIT = "STREAMLIT"


class Dashboard(BaseTyping):
    """Extends tihs class to create a dashboard.

    The sub class must implement the get_folder_path method to return the path of the folder containing the dashboard
    """

    @abstractmethod
    def get_app_folder_path(self) -> str:
        """
        :return: path of the folder containing the dashboard code
        :rtype: str
        """

    def get_app_type(self) -> StreamlitAppType:
        return "NORMAL"

    def get_env_file_path(self) -> str:
        return None


def dashboard_decorator(unique_name: str,
                        dashboard_type: DashboardType,
                        human_name: str = "",
                        short_description: str = "") -> Callable:
    """ Decorator to declare a dashboard folder.

    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type unique_name: str
    :param dashboard_type: type of the dashboard
    :type dashboard_type: DashboardType
    :param human_name: optional name that will be used in the interface when viewing the tasks.
                        If not defined, the unique_name will be used
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the tasks. Must not be longer than 255 caracters.
    :type short_description: str, optional

    """
    def decorator(task_class: Type[Dashboard]):
        _decorate_dashboard(task_class,
                            dashboard_type=dashboard_type,
                            unique_name=unique_name,
                            human_name=human_name,
                            short_description=short_description)

        return task_class
    return decorator


def _decorate_dashboard(
        dashboard_class: Type[Dashboard],
        dashboard_type: DashboardType,
        unique_name: str,
        human_name: str = "",
        short_description: str = "",):
    """Method to decorate a task
    """
    if not Utils.issubclass(dashboard_class, Dashboard):
        BrickService.log_brick_error(
            dashboard_class,
            f"The dashboard_decorator is used on the class: {dashboard_class.__name__} and this class is not a sub class of Dashboard")
        return

    if not isinstance(dashboard_type, DashboardType):
        BrickService.log_brick_error(
            dashboard_class,
            f"The dashboard_type: {dashboard_type} is not a instance of DashboardType")
        return

    register_gws_typing_class(object_class=dashboard_class,
                              object_type="DASHBOARD",
                              unique_name=unique_name,
                              object_sub_type=dashboard_type.value,
                              human_name=human_name,
                              short_description=short_description,
                              hide=True,
                              style=TypingStyle.default_task(),
                              deprecated=None)
