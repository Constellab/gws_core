# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_types import ConfigParamsDict
from gws_core.core.classes.rich_text_content import RichText
from gws_core.report.report import Report
from gws_core.report.report_service import ReportService
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view.view_dto import CallViewResult


@resource_decorator("ReportResource", human_name="Report resource", short_description="Report resource")
class ReportResource(Resource):

    report_id: str = StrRField()

    _report: Report = None
    _content: RichText = None

    def __init__(self, report_id: str = None):
        super().__init__()
        self.report_id = report_id

    def _get_content(self) -> RichText:
        if self._content is None:
            self._content = self._get_report().get_content_as_rich_text()
        return self._content

    def _get_report(self) -> Report:
        if self._report is None:
            self._report = Report.get_by_id_and_check(self.report_id)
        return self._report

    def replace_variable(self, variable_name: str, value: str) -> None:
        rich_text: RichText = self._get_content()
        rich_text.replace_variable(variable_name, value)
        self._content = rich_text

    def add_paragraph(self, paragraph: str) -> None:
        rich_text: RichText = self._get_content()
        rich_text.add_paragraph(paragraph)
        self._content = rich_text

    def add_view(self, resource: Resource, view_method_name: str, view_params: ConfigParamsDict = None,
                 title: str = None, caption: str = None) -> None:
        view_result: CallViewResult = ResourceService.get_and_call_view_on_resource_model(
            resource._model_id, view_method_name, view_params, True)

        rich_text: RichText = self._get_content()
        rich_text.append_resource_views(view_result.view_config.to_rich_text_resource_view(title, caption))
        self._content = rich_text

    def update_title(self, title: str) -> None:
        self._report = ReportService.update_title(self.report_id, title)

    def save(self):
        report = ReportService.update_content(self.report_id, self._get_content().get_content())
        self._content = report.get_content_as_rich_text()
