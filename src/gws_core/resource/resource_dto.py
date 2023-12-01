# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime

from typing_extensions import NotRequired, TypedDict


class ResourceDictDTO(TypedDict):
    id: str

    created_at: datetime
    created_by: dict
    last_modified_at: datetime
    last_modified_by: dict
    resource_typing_name: str
    resource_type_human_name: NotRequired[str]
    resource_type_short_description: NotRequired[str]
    fs_node: NotRequired[dict]
    is_downloadable: NotRequired[bool]
    origin: str
    name: str
    has_children: NotRequired[bool]
    type_status: str
    flagged: bool
    experiment: NotRequired[dict]
    project: NotRequired[dict]
