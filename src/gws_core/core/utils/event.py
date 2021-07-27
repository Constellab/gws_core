# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect

from ..exception.exceptions.bad_request_exception import BadRequestException


class EventListener:
    """
    EventListener class.
    """

    _events: dict = None

    def __init__(self):

        self._events = {}

    def sync_call(self, name: str, *args, **kwargs):
        """
        Calls an event function by its name

        :param name: Name of the event
        :type name: `str`
        """

        for func in self._events.get(name, []):
            if not inspect.iscoroutinefunction(func):
                func(*args, **kwargs)

    async def async_call(self, name: str, *args, **kwargs):
        """
        Calls an async event function by its name

        :param name: Name of the event
        :type name: `str`
        """

        for func in self._events.get(name, []):
            if inspect.iscoroutinefunction(func):
                await func(*args, **kwargs)

    def add(self, name: str, callback: callable):
        """
        Adds an event (i.e. callback function) to the listener

        :param name: The name of the event
        :type name: `str`
        :param callback: The callback function of the event
        :type callback: `function`
        """

        # @TODO
        # Also check that callback is awaitable
        # if not inspect.iscoroutinefunction(callback):
        #     raise BadRequestException("The callback must be an awaitable function"))

        if not hasattr(callback, '__call__'):
            raise BadRequestException("The callback function is not callable")

        if self.exists(name):
            self._events[name].append(callback)
        else:
            self._events[name] = [callback]

    def exists(self, name: str) -> bool:
        """
        Returns True if an event exists, False otherwise

        :rtype: bool
        """
        return name in self._events
