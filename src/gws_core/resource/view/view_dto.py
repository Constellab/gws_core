# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.resource.view.view_types import ViewType
from gws_core.resource.view_config.view_config_dto import ViewConfigDTO


class ResourceViewMetadatalDTO(BaseModelDTO):
    method_name: str
    view_type: ViewType
    human_name: str
    short_description: str
    default_view: bool
    has_config_specs: bool
    config_specs: dict


class CallViewResultDTO(BaseModelDTO):
    view: dict
    resource_id: str
    view_config: ViewConfigDTO
    title: str
    view_type: ViewType
