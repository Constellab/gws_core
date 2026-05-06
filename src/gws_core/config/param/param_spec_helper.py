from itertools import chain
from typing import Any

from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException

from .param_spec import ParamSpec
from .param_spec_decorator import (
    PARAM_SPEC_TYPES_BY_CATEGORY,
    ParamSpecCategory,
)
from .param_types import (
    ParamSpecType,
    ParamSpecTypeInfo,
)


class ParamSpecHelper:
    @staticmethod
    def create_param_spec_from_json(json_: dict[str, Any], validate: bool = False) -> ParamSpec:
        spec_dto = ParamSpecDTO.from_json(json_)

        return ParamSpecHelper.create_param_spec_from_dto(spec_dto, validate=validate)

    @staticmethod
    def create_param_spec_from_dto(dto: ParamSpecDTO, validate: bool = False) -> ParamSpec:
        param_spec_type = ParamSpecHelper.get_param_spec_type_from_str(dto.type)

        return param_spec_type.load_from_dto(dto, validate=validate)

    @staticmethod
    def get_param_spec_type_from_str(type_: ParamSpecType) -> type[ParamSpec]:
        for param_spec_type in ParamSpecHelper.get_param_spec_types():
            if param_spec_type.get_param_spec_type() == type_:
                return param_spec_type

        raise BadRequestException(f"Invalid param spec str type '{type_}'")

    @staticmethod
    def get_param_spec_types() -> list[type[ParamSpec]]:
        return list(chain.from_iterable(PARAM_SPEC_TYPES_BY_CATEGORY.values()))

    @staticmethod
    def get_param_spec_types_by_category(
        category: ParamSpecCategory,
    ) -> list[type[ParamSpec]]:
        return PARAM_SPEC_TYPES_BY_CATEGORY[category]

    @staticmethod
    def get_param_spec_types_info(
        categories: list[ParamSpecCategory],
    ) -> list[ParamSpecTypeInfo]:
        """Return the param spec type infos for the given categories.

        :param categories: categories whose spec types should be included.
        :return: list of param spec info specs.
        """
        return [
            spec_type.to_param_spec_info_specs()
            for category in categories
            for spec_type in PARAM_SPEC_TYPES_BY_CATEGORY[category]
        ]
