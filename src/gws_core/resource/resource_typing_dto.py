

from typing import Dict, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.reflector_types import MethodDoc
from gws_core.model.typing_dto import TypingFullDTO
from gws_core.resource.view.view_dto import ResourceViewMetadatalDTO


class ResourceTypingMethodDTO(BaseModelDTO):
    funcs: Optional[List[MethodDoc]]
    views: Optional[List[ResourceViewMetadatalDTO]]


class ResourceTypingVariableDTO(BaseModelDTO):
    name: str
    type: str
    doc: str


class ResourceTypingDTO(TypingFullDTO):
    variables: Optional[Dict]
    methods: Optional[ResourceTypingMethodDTO]
