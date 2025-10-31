

from dataclasses import dataclass
from typing import Literal

from gws_core.model.event.base_event import BaseEvent
from gws_core.user.user import User

# ============================================================================
# BASE USER EVENT
# ============================================================================

@dataclass
class BaseUserEvent(BaseEvent):
    """Base class for all user events with common fields"""
    type: Literal['user'] = 'user'
    action: str = ''
    data: User = None


# ============================================================================
# USER EVENTS
# ============================================================================

@dataclass
class UserCreatedEvent(BaseUserEvent):
    """Event dispatched when a user is created"""
    action: Literal['created'] = 'created'


@dataclass
class UserActivatedEvent(BaseUserEvent):
    """Event dispatched when a user is activated"""
    action: Literal['activated'] = 'activated'
    activated: bool = True


@dataclass
class UserUpdatedEvent(BaseUserEvent):
    """Event dispatched when a user is updated"""
    action: Literal['updated'] = 'updated'


# ============================================================================
# UNION TYPE
# ============================================================================

UserEvent = (
    UserCreatedEvent |
    UserActivatedEvent |
    UserUpdatedEvent
)
