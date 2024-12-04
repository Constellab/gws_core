

from typing import Any, Dict, List, Literal, Optional, Type

from gws_core.core.model.model_dto import BaseModelDTO

ParamValue = Any
ParamValueType = Type[ParamValue]


# Visibility of a param
# Public --> main param visible in the first config section in the interface
# Protected --> considered as advanced param, it will be in the advanced section in the interface (it must have a default value or be optional)
# Private --> private param, it will not be visible in the interface (it must have a default value or be optional)
ParamSpecVisibilty = Literal["public", "protected", "private"]


class ParamSpecSimpleDTO(BaseModelDTO):
    type: str
    optional: bool
    visibility: Optional[ParamSpecVisibilty] = "public"
    default_value: Optional[ParamValue] = None
    additional_info: Optional[Dict] = {}


class ParamSpecDTO(ParamSpecSimpleDTO):
    human_name: Optional[str] = None
    short_description: Optional[str] = None
    allowed_values: Optional[List[ParamValue]] = None


class ParamSpecInfoSpecs(BaseModelDTO):
    optional: ParamSpecDTO
    visibility: ParamSpecDTO
    human_name: ParamSpecDTO
    short_description: ParamSpecDTO
    default_value: Optional[ParamSpecDTO] = None
    additional_info: Optional[Dict[str, ParamSpecDTO]] = None


DynamicParamAllowedSpecsDict = Dict[str, ParamSpecInfoSpecs]
# TODO @vfoex remove following types
DynamicParamAllowedSpecsDict = Dict[str, ParamSpecDTO | Dict[str, ParamSpecDTO]]
