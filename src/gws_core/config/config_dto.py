from typing import Any

from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO


class ConfigDTO(ModelWithUserDTO):
    """
    ConfigDTO class.
    """

    specs: dict[str, ParamSpecDTO]
    values: dict[str, Any]


class ConfigSimpleDTO(BaseModelDTO):
    """
    ConfigDTO class.
    """

    specs: dict[str, ParamSpecDTO]
    values: dict[str, Any]
