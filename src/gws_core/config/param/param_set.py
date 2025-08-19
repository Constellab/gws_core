

from typing import Any, Dict, List, Optional

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec_decorator import (ParamSpecType,
                                                        param_spec_decorator)
from gws_core.core.utils.logger import Logger

from ...core.classes.validator import DictValidator, ListValidator
from .param_spec import ParamSpec
from .param_types import ParamSpecDTO, ParamSpecTypeStr, ParamSpecVisibilty


@param_spec_decorator(type_=ParamSpecType.NESTED)
class ParamSet(ParamSpec):
    """ ParamSet. Use to define a group of parameters that can be added multiple times. This will
    provid a list of dictionary as values : List[Dict[str, Any]]

    """

    param_set: ConfigSpecs = None
    max_number_of_occurrences: int

    def __init__(
        self,
        param_set: ConfigSpecs = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: Optional[str] = None,
        short_description: Optional[str] = None,
        max_number_of_occurrences: int = -1
    ):
        """
        :param optional: It true, the param_set can have 0 occurence, the value will then be an empty array [].
        :type optional: Optional[str]
        :param visibility: Visibility of the param. It override all child spec visibility. see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :param human_name: Human readable name of the param, showed in the interface
        :type human_name: Optional[str]
        :param short_description: Description of the param, showed in the interface
        :type short_description: Optional[str]
        :param max_number_of_occurrences: Nb max of occurence of values the params. If negative, there is no limit.
        :type max_number_of_occurrences: Optional[str]
        """

        self.max_number_of_occurrences = max_number_of_occurrences

        if param_set is None:
            param_set = ConfigSpecs()

        if isinstance(param_set, dict):
            Logger.warning("ParamSet: param_set should be a ConfigSpecs object, not a dict. ")
            param_set = ConfigSpecs(param_set)

        self.param_set = param_set
        super().__init__(
            default_value=[] if optional else None,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    def get_default_value(self) -> List:
        if self.optional:
            return []

        # if this is not optional, return an array of 1 element with the
        # default value of each param_spec
        return [self.param_set.get_default_values()]

    def validate(self, value: List[Dict[str, Any]]) -> Any:
        if value is None:
            return []
        list_validator = ListValidator(max_number_of_occurrences=self.max_number_of_occurrences)
        dict_validator = DictValidator()

        # global validation of the list
        list_: List[Dict[str, Any]] = list_validator.validate(value)

        result_list = []
        for dict_ in list_:
            # Valid on dict of param set
            dict_ = dict_validator.validate(dict_)

            validated_item = self.param_set.get_and_check_values(dict_)
            result_list.append(validated_item)

        return result_list

    def to_dto(self) -> ParamSpecDTO:
        json_: ParamSpecDTO = super().to_dto()

        # convert the additional info to json
        json_.additional_info = {
            "max_number_of_occurrences": self.max_number_of_occurrences,
            "param_set": self.param_set.to_dto()
        }

        return json_

    @classmethod
    def get_str_type(cls) -> ParamSpecTypeStr:
        return ParamSpecTypeStr.PARAM_SET

    @classmethod
    def load_from_dto(cls, spec_dto: ParamSpecDTO) -> "ParamSet":
        from .param_spec_helper import ParamSpecHelper
        param_set: ParamSet = super().load_from_dto(spec_dto)

        # load info from additional info
        param_set.max_number_of_occurrences = spec_dto.additional_info.get("max_number_of_occurrences")

        specs = ConfigSpecs()

        for key, param in spec_dto.additional_info.get("param_set").items():
            specs.add_spec(key, ParamSpecHelper.create_param_spec_from_json(param))

        param_set.param_set = specs

        return param_set

    @classmethod
    def get_default_value_param_spec(cls) -> "ParamSet":
        return ParamSet()

    @classmethod
    def get_additional_infos(cls) -> Dict[str, ParamSpecDTO]:
        return None
