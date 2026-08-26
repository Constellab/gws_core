from datetime import datetime
from enum import Enum
from typing import Any

from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.io.io_spec import IOSpecDTO
from gws_core.model.typing_style import TypingStyle
from gws_core.tag.tag_dto import TagValueFormat


class HnRepoType(str, Enum):
    PIP = "PIP"
    GIT = "GIT"


class HnBrickVersionInfoDTO(BaseModelDTO):
    brickName: str  # noqa: N815
    brickVersion: str  # noqa: N815
    repoType: HnRepoType  # noqa: N815
    repositoryUrl: str  # noqa: N815
    technicalInfo: dict[str, Any] | None = None  # noqa: N815


class HnNode(BaseModelDTO):
    """A node in a brick's documentation hierarchy tree.

    ``name``, ``path`` and ``completePath`` are ``None`` on the virtual root node
    returned by the API (whose only meaningful content is its ``children``).
    """

    id: str
    name: str | None = None
    order: int
    path: str | None = None
    completePath: str | None = None  # noqa: N815
    parentId: str | None = None  # noqa: N815
    children: list["HnNode"] | None = None


class CommunitySpaceDTO(BaseModelDTO):
    id: str
    name: str


class CommunityAgentDTO(BaseModelDTO):
    id: str
    title: str
    space: CommunitySpaceDTO | None = None
    created_at: str | None = None
    last_modified_at: str | None = None
    created_by: object | None = None
    latest_publish_version: int
    description: object | None = None
    latest_style: TypingStyle | None = None
    agent_co_authors: list[object] | None = None
    likes: int | None = None
    comments: int | None = None


class CommunityAgentFileParams(BaseModelDTO):
    specs: dict[str, ParamSpecDTO]
    values: dict[str, Any]


class CommunityAgentFileDTO(BaseModelDTO):
    json_version: int
    params: CommunityAgentFileParams
    code: str
    environment: str
    input_specs: dict
    output_specs: dict
    config_specs: dict
    bricks: list[dict]
    task_type: str
    style: TypingStyle


class CommunityAgentIOSpecDTO(BaseModelDTO):
    # TODO type to improve, it is not standard
    specs: dict[str, IOSpecDTO]


class CommunityAgentVersionDTO(BaseModelDTO):
    id: str
    version: int
    type: str
    environment: str | None
    params: dict[str, Any] | None
    code: str
    input_specs: CommunityAgentIOSpecDTO | None
    output_specs: CommunityAgentIOSpecDTO | None
    config_specs: dict | None
    agent: CommunityAgentDTO
    style: TypingStyle | None = None


class CommunityCreateAgentDTO(BaseModelDTO):
    title: str
    type: str
    space: Any


class CommunityGetAgentsBody(BaseModelDTO):
    spacesFilter: list[str] = []  # noqa: N815
    titleFilter: str = ""  # noqa: N815
    personalOnly: bool = False  # noqa: N815


class CommunityAgentVersionCreateResDTO(BaseModelDTO):
    id: str
    agent_version: str
    title: str


class CommunityTagKeyDTO(BaseModelDTO):
    id: str
    key: str
    label: str | None = None
    value_format: TagValueFormat
    deprecated: bool
    published_at: str | None = None
    unit: str | None = None
    description: RichTextDTO | None = None
    space: CommunitySpaceDTO | None = None
    tag_co_authors: list[object] | None = None
    created_at: str | None = None
    last_modified_at: str | None = None
    created_by: object | None = None
    last_modified_by: object | None = None
    additional_infos_specs: dict[str, Any] | None = None


class CommunityGetTagKeysBody(BaseModelDTO):
    spacesFilter: list[str] = []  # noqa: N815
    labelFilter: str = ""  # noqa: N815
    personalOnly: bool = False  # noqa: N815


class CommunityTagValueDTO(BaseModelDTO):
    id: str
    value: str
    deprecated: bool
    tag_key: CommunityTagKeyDTO
    short_description: str | None = None
    additional_infos: dict[str, Any] | None = None


class CommunityRagflowAskResponseDTO(BaseModelDTO):
    """Response from the ragflow-chatbot/ask endpoint."""

    answer: str
    session_id: str
    references: list[dict] = []


class CommunityUserDTO(BaseModelDTO):
    id: str
    alias: str
    userCode: str  # noqa: N815
    photo: str | None = None


class CommunityDocumentationDTO(BaseModelDTO):
    """Response from the GET /documentation/:id endpoint."""

    id: str
    createdAt: datetime  # noqa: N815
    createdBy: CommunityUserDTO  # noqa: N815
    lastModifiedAt: datetime  # noqa: N815
    lastModifiedBy: CommunityUserDTO  # noqa: N815
    title: str
    content: RichTextDTO
    path: str
    completePath: str  # noqa: N815
    order: int


class CommunityCreateDocResponseDTO(BaseModelDTO):
    """Response from the POST /folder/doc endpoint when creating a documentation page.

    A freshly created page has no content yet (``content`` is ``None``). The response
    also embeds the parent ``folder`` (with all its sibling documentations); it is kept
    as a loose dict since only the created page's own fields are needed here.
    """

    id: str
    title: str
    createdAt: datetime  # noqa: N815
    createdBy: CommunityUserDTO  # noqa: N815
    lastModifiedAt: datetime  # noqa: N815
    lastModifiedBy: CommunityUserDTO  # noqa: N815
    path: str
    completePath: str  # noqa: N815
    order: int
    content: RichTextDTO | None = None
    folder: dict | None = None
