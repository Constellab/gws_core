# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Optional

from ..core.classes.validator import DictValidator, ListValidator, Validator
from .param_spec import ParamSpec, ParamSpecType, ParamSpecVisibilty


class ParamSet(ParamSpec[list]):
    """ ParamSet. Use to define a group of parameters that can be added multiple times. This will
    provided a list of dictionary as values : List[Dict[str, Any]]

    """

    param_set: Dict[str, ParamSpec] = None
    max_number_of_occurrences: int

    def __init__(
        self,
        param_set: Dict[str, ParamSpec] = None,
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

    def _get_validator(self) -> Validator:
        """ There is not assigne validator, instead the validate method has been overrided
        """
        return None

    def validate(self, value: List[Dict[str, Any]]) -> ParamSpecType:
        if value is None:
            return None
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

    def to_json(self) -> Dict[str, Any]:
        json_: Dict[str, Any] = super().to_json()

        json_["max_number_of_occurrences"] = self.max_number_of_occurrences
        json_["param_set"] = {}

        for key, spec in self.param_set.items():
            json_["param_set"][key] = spec.to_json()

        return json_

    @classmethod
    def get_str_type(cls) -> str:
        return "param_set"

    @classmethod
    def load_from_json(cls, json_: Dict[str, Any]) -> "ParamSet":
        from .param_spec_helper import ParamSpecHelper
        param_spec: ParamSet = super().load_from_json(json_)
        param_spec.max_number_of_occurrences = json_.get("max_number_of_occurrences")
        param_spec.param_set = {}

        for key, param in json_["param_set"].items():
            param_spec.param_set[key] = ParamSpecHelper.create_param_spec_from_json(param)

        return param_spec