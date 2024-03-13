
from typing import Any, Optional

from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_spec_decorator import param_spec_decorator
from gws_core.config.param.param_types import ParamSpecVisibilty
from gws_core.core.classes.validator import StrValidator


@param_spec_decorator()
class ReportParam(ParamSpec[str]):
    """ Report params spec. When used, the end user will be able to select a report
    from the list of report available in the lab.

    The accessible value will be ReportResource.

    """

    def __init__(self,
                 optional: bool = False,
                 visibility: ParamSpecVisibilty = "public",
                 human_name: Optional[str] = "Select report",
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
        return "report_param"

    def build(self, value: Any) -> dict:
        from gws_core.report.report import Report
        from gws_core.report.task.report_resource import ReportResource
        report: Report = None
        if value and isinstance(value, str):

            # retrieve the report template and return it
            report = Report.get_by_id(value)
            if report is None:
                raise Exception(f"Report with id '{value}' not found")

        return ReportResource(report_id=report.id) if report else None

    def validate(self, value: Any) -> str:
        from gws_core.report.task.report_resource import ReportResource
        if isinstance(value, ReportResource):
            return value.report_id
        # if this is the credentials object, retrieve the name
        if isinstance(value, dict) and 'id' in value:
            value = value['id']

        validator = StrValidator()
        return validator.validate(value)
