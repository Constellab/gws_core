

from typing import Callable, Type

from ..model.typing_register_decorator import register_typing_class
from .process import Process
from .process_model import ProcessAllowedUser


def ProcessDecorator(unique_name: str, allowed_user: ProcessAllowedUser = ProcessAllowedUser.ALL,
                     human_name: str = "", short_description: str = "", hide: bool = False) -> Callable:
    """ Decorator to be placed on all the processes. A process not decorated will not be runnable.
    It define static information about the process

    :param name_unique: a unique name for this process in the brick. Only 1 process in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the processes
    :type name_unique: str
    :param allowed_user: role needed to run the process. By default all user can run it. It Admin, the user need to be an admin of the lab to run the process
    :type allowed_user: ProtocolAllowedUser, optional
    :param human_name: optional name that will be used in the interface when viewing the processes. Must not be longer than 20 caracters
                        If not defined, the name_unique will be used
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the processes. Must not be longer than 100 caracters
    :type short_description: str, optional
    :param hide: Only the process will hide=False will be available in the interface, other will be hidden.
                It is useful for process that are not meant to be viewed in the interface (like abstract classes), defaults to False
    :type hide: bool, optional

    """
    def decorator(process_class: Type[Process]):
        if not issubclass(process_class, Process):
            raise Exception(
                f"The ProcessDecorator is used on the class: {process_class.__name__} and this class is not a sub class of Process")

        register_typing_class(object_class=process_class, object_type="PROCESS", unique_name=unique_name,
                              human_name=human_name, short_description=short_description, hide=hide)

        # set the allowed user for the process
        process_class._allowed_user = allowed_user

        return process_class
    return decorator
