from typing import Any

from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException

from .param_spec import ParamSpec
from .param_spec_decorator import (
    LAB_SPECIFIC_PARAM_SPEC_TYPES_LIST,
    NESTED_PARAM_SPEC_TYPES_LIST,
    PARAM_SPEC_TYPES_LIST,
    SIMPLE_PARAM_SPEC_TYPES_LIST,
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
        param_spec_types = ParamSpecHelper._get_param_spec_types()
        for param_spec_type in param_spec_types:
            if param_spec_type.get_param_spec_type() == type_:
                return param_spec_type

        raise BadRequestException(f"Invalid param spec str type '{type_}'")

    @staticmethod
    def _get_param_spec_types() -> list[type[ParamSpec]]:
        return PARAM_SPEC_TYPES_LIST

    @staticmethod
    def get_simple_param_spec_types() -> list[type[ParamSpec]]:
        return SIMPLE_PARAM_SPEC_TYPES_LIST

    @staticmethod
    def get_lab_specific_param_spec_types() -> list[type[ParamSpec]]:
        return LAB_SPECIFIC_PARAM_SPEC_TYPES_LIST

    @staticmethod
    def get_nested_param_spec_types() -> list[type[ParamSpec]]:
        return NESTED_PARAM_SPEC_TYPES_LIST

    @staticmethod
    def get_dynamic_param_allowed_param_spec_types(
        lab_allowed: bool = False,
    ) -> list[ParamSpecTypeInfo]:
        """Return the list of param spec types allowed in a dynamic param.

        :param lab_allowed: if True, lab-specific param spec types are included, defaults to False
        :type lab_allowed: bool, optional
        :return: list of allowed param spec info specs
        :rtype: list[ParamSpecInfoSpecs]
        """
        res: list[ParamSpecTypeInfo] = [
            spec_type.to_param_spec_info_specs()
            for spec_type in ParamSpecHelper.get_simple_param_spec_types()
        ]

        if lab_allowed:
            res.extend(
                spec_type.to_param_spec_info_specs()
                for spec_type in ParamSpecHelper.get_lab_specific_param_spec_types()
            )

        return res
