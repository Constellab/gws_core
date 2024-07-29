

from gws_core.config.config_types import ConfigParamsDict
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextObjectType
from gws_core.impl.rich_text.rich_text_view import RichTextView
from gws_core.model.typing_style import TypingStyle
from gws_core.report.report import Report
from gws_core.report.report_service import ReportService
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view.view_decorator import view
from gws_core.resource.view.view_result import CallViewResult


@resource_decorator("ReportResource", human_name="Report resource", short_description="Report resource",
                    style=TypingStyle.material_icon("report", background_color="#735f32"))
class ReportResource(Resource):

    report_id: str = StrRField()

    _report: Report = None
    _content: RichText = None

    def __init__(self, report_id: str = None):
        super().__init__()
        self.report_id = report_id

    def get_content(self) -> RichText:
        if self._content is None:
            self._content = self.get_report().get_content_as_rich_text()
        return self._content

    def get_report(self) -> Report:
        if self._report is None:
            self._report = Report.get_by_id_and_check(self.report_id)
        return self._report

    def replace_variable(self, variable_name: str, value: str) -> None:
        rich_text: RichText = self.get_content()
        rich_text.set_parameter(variable_name, value)
        self._content = rich_text

    def add_paragraph(self, paragraph: str) -> None:
        rich_text: RichText = self.get_content()
        rich_text. add_paragraph(paragraph)
        self._content = rich_text

    def add_view(self, resource: Resource, view_method_name: str, config_values: ConfigParamsDict = None,
                 title: str = None, caption: str = None, variable_name: str = None) -> None:
        view_result: CallViewResult = ResourceService.get_and_call_view_on_resource_model(
            resource._model_id, view_method_name, config_values, True)

        rich_text: RichText = self.get_content()
        rich_text.add_resource_view(view_result.view_config.to_rich_text_resource_view(title, caption), variable_name)
        self._content = rich_text

    def update_title(self, title: str) -> None:
        self._report = ReportService.update_title(self.report_id, title)

    def save(self):
        report = ReportService.update_content(self.report_id, self.get_content().get_content())
        self._content = report.get_content_as_rich_text()

    @view(view_type=RichTextView, human_name="View report", short_description="View report content", default_view=True)
    def view_report(self, config: ConfigParamsDict = None) -> RichTextView:
        return RichTextView(self.get_report().title,
                            self.get_content(),
                            object_type=RichTextObjectType.REPORT,
                            object_id=self.report_id)
