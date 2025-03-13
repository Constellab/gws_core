
from typing import Any, Dict, Optional

from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_spec_decorator import (ParamaSpecType,
                                                        param_spec_decorator)
from gws_core.config.param.param_types import (ParamSpecDTO, ParamSpecTypeStr,
                                               ParamSpecVisibilty)
from gws_core.core.classes.validator import StrValidator
from gws_core.scenario.scenario import Scenario


@param_spec_decorator(type_=ParamaSpecType.LAB_SPECIFIC)
class ScenarioParam(ParamSpec[str]):
    """ Scenario param spec. When used, the end user will be able to select a scenario from
    the list of available scenarios. The config stores only the scenario id, not the full scenario object.

    The accessible value in task is a Scenario.
    See the documentation of the credentials type for more info.

    """

    def __init__(self,
                 optional: bool = False,
                 visibility: ParamSpecVisibilty = "public",
                 human_name: Optional[str] = 'Select a scenario',
                 short_description: Optional[str] = None,
                 ):
        """
        :param optional: See default value
        :type optional: Optional[str]
        :param visibility: Visibility of the param, see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :param human_name: Human readable name of the param, showed in the interface
        :type human_name: Optional[str]
        :param short_description: Description of the param, showed in the interface
        :type short_description: Optional[str]
        """

        super().__init__(
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    @classmethod
    def get_str_type(cls) -> ParamSpecTypeStr:
        return ParamSpecTypeStr.SCENARIO

    def build(self, value: Any) -> Scenario:
        if not value:
            return None

        return Scenario.get_by_id_and_check(value)

    def validate(self, value: Any) -> str:

        if isinstance(value, Scenario):
            return value.id
        # if this is the credentials object, retrieve the name
        if isinstance(value, dict) and 'id' in value:
            value = value['id']

        validator = StrValidator()
        return validator.validate(value)

    @classmethod
    def get_default_value_param_spec(cls) -> "ScenarioParam":
        return ScenarioParam()

    @classmethod
    def get_additional_infos(cls) -> Dict[str, ParamSpecDTO]:
        return None
