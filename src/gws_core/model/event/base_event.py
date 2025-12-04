from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gws_core.user.user import User


@dataclass
class BaseEvent:
    """Base class for all events in the system.

    All events must have:
    - type: The type of the event (e.g., 'user', 'experiment', 'project', 'system')
    - action: The action that occurred (e.g., 'created', 'updated', 'activated')
    - data: The main data of the event (e.g., the entity or data involved)
    - timestamp: When the event occurred
    - triggered_by: The user who triggered this action (None for system actions)

    Example:
        @dataclass
        class UserCreatedEvent(BaseEvent):
            type: Literal['user'] = 'user'
            action: Literal['created'] = 'created'
            data: User = None
            triggered_by: User | None = None
    """

    type: str = ""
    """The type of event (e.g., 'user', 'experiment', 'project', 'system')"""

    action: str = ""
    """The action that occurred (e.g., 'created', 'updated', 'deleted')"""

    data: any = None
    """The main data of the event (e.g., the entity or data involved)"""

    timestamp: datetime = field(default_factory=datetime.now)
    """When the event occurred"""

    triggered_by: "User | None" = None
    """The user who triggered this action (None for system actions)"""

    def get_event_name(self) -> str:
        """Get the full event name in format 'type.action'

        :return: Event name (e.g., 'user.created')
        :rtype: str
        """
        return f"{self.type}.{self.action}"

    def __repr__(self) -> str:
        triggered_by_str = self.triggered_by.email if self.triggered_by else "system"
        return (
            f"{self.__class__.__name__}("
            f"type='{self.type}', "
            f"action='{self.action}', "
            f"triggered_by='{triggered_by_str}', "
            f"timestamp={self.timestamp})"
        )
