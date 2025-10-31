

from dataclasses import dataclass
from typing import Literal

from gws_core.model.event.base_event import BaseEvent


@dataclass
class BaseSystemEvent(BaseEvent):
    """Base class for all system events with common fields"""
    type: Literal['system'] = 'system'
    action: str = ''

@dataclass
class SystemStartedEvent(BaseSystemEvent):
    """Event dispatched when the system is started"""
    action: Literal['started'] = 'started'
    data: None = None


SystemEvent = (
    SystemStartedEvent
)