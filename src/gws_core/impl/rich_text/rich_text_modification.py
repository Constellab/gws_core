from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockType
from gws_core.impl.rich_text.rich_text_types import RichTextDTO


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

# export interface TeNewFullRichTextDTO {
#   version: number;
#   richText: TeRichTextDTO;
#   mo/difications?: TeRichTextBlockModificationsDTO;
# }


class RichTextAggregateDTO(BaseModelDTO):
    """Class to represent a rich text with its modifications
    Used in space note

    :param BaseModelDTO: _description_
    :type BaseModelDTO: _type_
    :return: _description_
    :rtype: _type_
    """
    version: int
    richText: RichTextDTO
    modifications: Optional[Any] = None

    @classmethod
    def json_is_rich_text_aggregate(cls, dict_: dict) -> bool:
        if 'version' not in dict_ or 'richText' not in dict_:
            return False

        try:
            RichTextAggregateDTO.from_json(dict_)
        except Exception:
            return False
        return True
