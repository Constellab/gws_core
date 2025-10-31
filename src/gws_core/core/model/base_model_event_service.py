from typing import List

from gws_core.core.db.thread_db import ThreadDb
from gws_core.core.model.base_model import BaseModel
from gws_core.core.utils.logger import Logger
from pyparsing import abstractmethod


class BaseModelEventType:
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'

class BaseModelEvent():
    type: BaseModelEventType
    model: BaseModel

class BaseModelEventObserver:
    """Observer to be notified of model events (create, update, delete)
    """

    @abstractmethod
    def update(self, events: List[BaseModelEvent]) -> None:
        """Called when an event is notified

        :param event: Event to notify
        :type event: BaseModelEvent
        """



class BaseModelEventService:
    """Service to manage model events (create, update, delete)
    """

    _observers: List[BaseModelEventObserver] = []
    _transaction_events: List[BaseModelEvent] = []


    @classmethod
    def notify_event(cls, event_type: BaseModelEventType, model: BaseModel) -> None:
        """Notify an event to the service

        :param event: Event to notify
        :type event: BaseModelEvent
        """
        if not cls._observers:
            return

        db_manager = model.get_db_manager()
        if db_manager is None:
            return

        if db_manager.has_transaction():
            cls._transaction_events.append(BaseModelEvent(type=event_type, model=model))
            db_manager.register_after_commit_hook(cls._after_transaction_commit)
        else:
            cls._notify_observers([BaseModelEvent(type=event_type, model=model)])

    @classmethod
    def _after_transaction_commit(cls) -> None:
        """Method called after a transaction is committed
        """
        cls._notify_observers(cls._transaction_events)
        cls._transaction_events = []

    @classmethod
    def _notify_observers(cls, events: List[BaseModelEvent]) -> None:
        """Notify all observers of the service

        :param events: Events to notify
        :type events: List[BaseModelEvent]
        """
        if not cls._observers:
            return
        thread = ThreadDb(target=cls._notify_observer_async, args=(events,))
        thread.daemon = True
        thread.start()

    @classmethod
    def _notify_observer_async(cls, events: List[BaseModelEvent]) -> None:
        """Notify all observers of the service in an async way

        :param events: Events to notify
        :type events: List[BaseModelEvent]
        """
        for observer in cls._observers:
            try:
                observer.update(events)
            except Exception as e:
                # Handle exception
                Logger.error(f"Error notifying observer {observer}: {e}")

    @classmethod
    def register_observer(cls, observer: BaseModelEventObserver) -> None:
        """Register an observer to the service

        :param observer: Observer to register
        :type observer: BaseModelEventObserver
        """
        if not isinstance(observer, BaseModelEventObserver):
            raise ValueError("Observer must be an instance of BaseModelEventObserver")
        if observer in cls._observers:
            return
        cls._observers.append(observer)

    @classmethod
    def unregister_observer(cls, observer: BaseModelEventObserver) -> None:
        """Unregister an observer from the service

        :param observer: Observer to unregister
        :type observer: BaseModelEventObserver
        """
        if observer in cls._observers:
            cls._observers.remove(observer)
