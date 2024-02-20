# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.refloctor_types import MethodDoc
from gws_core.model.typing_dto import TypingFullDTO
from gws_core.resource.view.view_dto import ResourceViewMetadatalDTO


class ResourceTypingMethodDTO(BaseModelDTO):
    funcs: Optional[List[MethodDoc]]
    views: Optional[List[ResourceViewMetadatalDTO]]


class ResourceTypingDTO(TypingFullDTO):
    methods: ResourceTypingMethodDTO
