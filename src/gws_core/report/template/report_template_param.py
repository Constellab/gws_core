# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import Any, Optional

from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_spec_decorator import param_spec_decorator
from gws_core.config.param.param_types import ParamSpecVisibilty
from gws_core.core.classes.validator import StrValidator
from gws_core.report.template.report_template import ReportTemplate


@param_spec_decorator()
class ReportTemplateParam(ParamSpec[str]):
    """ Report template params spec. When used, the end user will be able to select a report template
    from the list of report template available in the lab.

    The accessible value will be report template.

    """

    def __init__(self,
                 optional: bool = False,
                 visibility: ParamSpecVisibilty = "public",
                 human_name: Optional[str] = "Select report template",
                 short_description: Optional[str] = None,
                 ):
        """
        :param optional: See default value
        :type optional: Optional[str]
        :param visibility: Visibility of the param, see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :type default: Optional[ConfigParamType]
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
    def get_str_type(cls) -> str:
        return "report_template_param"

    def build(self, value: Any) -> dict:
        report_template: ReportTemplate = None
        if value and isinstance(value, str):

            # retrieve the report template and return it
            report_template = ReportTemplate.get_by_id(value)
            if report_template is None:
                raise Exception(f"Report template with id '{value}' not found")

        return report_template

    def validate(self, value: Any) -> str:
        if isinstance(value, ReportTemplate):
            return value.id
        # if this is the credentials object, retrieve the name
        if isinstance(value, dict) and 'id' in value:
            value = value['id']

        validator = StrValidator()
        return validator.validate(value)
