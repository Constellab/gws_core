# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Optional

from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec_decorator import param_spec_decorator

from ...core.classes.validator import DictValidator, ListValidator
from .param_spec import ParamSpec, ParamSpecType
from .param_types import ParamSpecDTO, ParamSpecVisibilty


@param_spec_decorator()
class ParamSet(ParamSpec[list]):
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
            param_set = {}
        self.param_set = param_set
        super().__init__(
            default_value=[] if optional else None,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    def get_default_value(self) -> ParamSpecType:
        if self.optional:
            return []

        # if this is not option, return an array of 1 element with the
        # default value of each param_spec
        default_value = {}
        for key, spec in self.param_set.items():
            default_value[key] = spec.get_default_value()
        return [default_value]

    def validate(self, value: List[Dict[str, Any]]) -> ParamSpecType:
        if value is None:
            return []
        list_validator = ListValidator(max_number_of_occurrences=self.max_number_of_occurrences)
        dict_validator = DictValidator()

        # global validation of the list
        list_: List[Dict[str, Any]] = list_validator.validate(value)
        index = 0
        for dict_ in list_:
            # Valid on dict of param set
            list_[index] = dict_validator.validate(dict_)

            # validate each value of the param set by retreiving the corresponding param_spec
            for key, spec in self.param_set.items():
                value: Any = dict_.get(key)

                dict_[key] = spec.validate(value)

            index = index + 1

        return list_

    def to_dto(self) -> ParamSpecDTO:
        json_: ParamSpecDTO = super().to_dto()

        # convert the additional info to json
        json_.additional_info = {
            "max_number_of_occurrences": self.max_number_of_occurrences,
            "param_set": {key: spec.to_dto() for key, spec in self.param_set.items()}
        }

        return json_

    @classmethod
    def get_str_type(cls) -> str:
        return "param_set"

    @classmethod
    def load_from_dto(cls, spec_dto: ParamSpecDTO) -> "ParamSet":
        from .param_spec_helper import ParamSpecHelper
        param_set: ParamSet = super().load_from_dto(spec_dto)

        # load info from additional info
        param_set.max_number_of_occurrences = spec_dto.additional_info.get("max_number_of_occurrences")

        for key, param in spec_dto.additional_info.get("param_set").items():
            param_set.param_set[key] = ParamSpecHelper.create_param_spec_from_json(param)

        return param_set
