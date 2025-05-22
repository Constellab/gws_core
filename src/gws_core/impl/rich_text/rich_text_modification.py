from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockType


class RichTextModificationType(Enum):
    """List the possible modification type in a rich text"""
    CREATED = 'CREATED'
    UPDATED = 'UPDATED'
    DELETED = 'DELETED'
    MOVED = 'MOVED'


class RichTextModificationDifferenceDTO(BaseModelDTO):
    index: int
    count: int
    added: bool
    removed: bool
    value: str


class RichTextBlockModificationDTO(BaseModelDTO):
    """Object representing a modification of a block in a rich text"""
    id: str
    time: datetime
    blockId: str
    blockType: RichTextBlockType
    differences: Optional[List[RichTextModificationDifferenceDTO]] = None
    blockValue: Optional[Dict[str, Any]] = None
    type: RichTextModificationType
    index: int
    oldIndex: Optional[int] = None
    userId: str


class RichTextModificationUserDTO(BaseModelDTO):
    id: str
    firstname: str
    lastname: str
    photo: Optional[str] = None


class RichTextBlockModificationWithUserDTO(RichTextBlockModificationDTO):
    user: RichTextModificationUserDTO


class RichTextModificationsDTO(BaseModelDTO):
    version: int = 1
    modifications: List[RichTextBlockModificationDTO] = []
