from typing import Any, Dict, List, Optional

from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.io.io_spec import IOSpecDTO
from gws_core.model.typing_style import TypingStyle
from gws_core.tag.tag_dto import TagValueFormat


class CommunitySpaceDTO(BaseModelDTO):
    id: str
    name: str


class CommunityAgentDTO(BaseModelDTO):
    id: str
    title: str
    space: Optional[CommunitySpaceDTO] = None
    created_at: Optional[str] = None
    last_modified_at: Optional[str] = None
    created_by: Optional[object] = None
    latest_publish_version: int
    description: Optional[object] = None
    latest_style: Optional[TypingStyle] = None
    agent_co_authors: Optional[List[object]] = None
    likes: Optional[int] = None
    comments: Optional[int] = None


class CommunityAgentFileParams(BaseModelDTO):
    specs: Dict[str, ParamSpecDTO]
    values: Dict[str, Any]


class CommunityAgentFileDTO(BaseModelDTO):
    json_version: int
    params: CommunityAgentFileParams
    code: str
    environment: str
    input_specs: Dict
    output_specs: Dict
    config_specs: Dict
    bricks: List[Dict]
    task_type: str
    style: TypingStyle


class CommunityAgentIOSpecDTO(BaseModelDTO):
    # TODO type to improve, it is not standard
    specs: Dict[str, IOSpecDTO]


class CommunityAgentVersionDTO(BaseModelDTO):
    id: str
    version: int
    type: str
    environment: Optional[str]
    params: Optional[Dict[str, Any]]
    code: str
    input_specs: Optional[CommunityAgentIOSpecDTO]
    output_specs: Optional[CommunityAgentIOSpecDTO]
    config_specs: Optional[Dict]
    agent: CommunityAgentDTO
    style: Optional[TypingStyle] = None


class CommunityCreateAgentDTO(BaseModelDTO):
    title: str
    type: str
    space: Any


class CommunityGetAgentsBody(BaseModelDTO):
    spacesFilter: List[str] = []
    titleFilter: str = ''
    personalOnly: bool = False


class CommunityAgentVersionCreateResDTO(BaseModelDTO):
    id: str
    agent_version: str
    title: str


class CommunityTagKeyDTO(BaseModelDTO):
    id: str
    key: str
    label: str
    value_format: TagValueFormat
    deprecated: bool
    published_at: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[RichTextDTO] = None
    space: Optional[CommunitySpaceDTO] = None
    tag_co_authors: Optional[List[object]] = None
    created_at: Optional[str] = None
    last_modified_at: Optional[str] = None
    created_by: Optional[object] = None
    last_modified_by: Optional[object] = None
    additional_infos_specs: Optional[Dict[str, Any]] = None


class CommunityGetTagKeysBody(BaseModelDTO):
    spacesFilter: List[str] = []
    labelFilter: str = ''
    personalOnly: bool = False


class CommunityTagValueDTO(BaseModelDTO):
    id: str
    value: str
    deprecated: bool
    tag_key: CommunityTagKeyDTO
    short_description: Optional[str] = None
    additional_infos: Optional[Dict[str, Any]] = None
