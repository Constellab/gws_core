from typing import Any

from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.utils.string_helper import StringHelper

from .param_spec import ParamSpec
from .param_spec_decorator import (
    LAB_SPECIFIC_PARAM_SPEC_TYPES_LIST,
    NESTED_PARAM_SPEC_TYPES_LIST,
    PARAM_SPEC_TYPES_LIST,
    SIMPLE_PARAM_SPEC_TYPES_LIST,
    ParamSpecType,
)
from .param_types import (
    CompleteDynamicParamAllowedSpecsDict,
    ParamSpecTypeStr,
)


class ParamSpecHelper:
    @staticmethod
    def create_param_spec_from_json(json_: dict[str, Any]) -> ParamSpec:
        spec_dto = ParamSpecDTO.from_json(json_)

        return ParamSpecHelper.create_param_spec_from_dto(spec_dto)

    @staticmethod
    def create_param_spec_from_dto(dto: ParamSpecDTO) -> ParamSpec:
        param_spec_type = ParamSpecHelper.get_param_spec_type_from_str(dto.type)

        return param_spec_type.load_from_dto(dto)

    @staticmethod
    def get_param_spec_type_from_str(type_: ParamSpecTypeStr) -> type[ParamSpec]:
        param_spec_types = ParamSpecHelper._get_param_spec_types()
        for param_spec_type in param_spec_types:
            if param_spec_type.get_str_type() == type_:
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
    ) -> CompleteDynamicParamAllowedSpecsDict:
        """_summary_

        :param lab_allowed: _description_, defaults to False
        :type lab_allowed: bool, optional
        :return: _description_
        :rtype: _type_
        """
        res: CompleteDynamicParamAllowedSpecsDict = {}
        key = StringHelper.snake_case_to_sentence(ParamSpecType.SIMPLE.value)
        res[key] = {}

        list_spec_types: list[type[ParamSpec]] = (
            ParamSpecHelper.get_simple_param_spec_types().copy()
        )

        for spec_type in list_spec_types:
            spec_name = spec_type.get_str_type()
            infos = spec_type.to_param_spec_info_specs()
            res[key][spec_name] = infos

        if lab_allowed:
            list_spec_types = ParamSpecHelper.get_lab_specific_param_spec_types()
            key = StringHelper.snake_case_to_sentence(ParamSpecType.LAB_SPECIFIC.value)
            res[key] = {}
            for spec_type in list_spec_types:
                spec_name = spec_type.get_str_type()
                infos = spec_type.to_param_spec_info_specs()
                res[key][spec_name] = infos

        return res
