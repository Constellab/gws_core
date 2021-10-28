

from typing import Callable

from .utils import Utils


class DecoratorHelper():

    @staticmethod
    def check_method_decorator(func: Callable) -> None:
        """Method to check that the func is valid for a method decorator.
        It throws an exception is not valid

        :param func: decorated function
        :type func: Callable
        """
        # check that the decorator is place after the @classmethod or @staticmethod decorator otherwise it does not work
        if hasattr(func, '__class__') and (
                Utils.issubclass(func.__class__, classmethod) or Utils.issubclass(func.__class__, staticmethod)):
            raise Exception("The @import_from_path decorator must be placed after the @classmethod decorator")
