# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_types import ConfigParamsDict
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_view import RichTextView
from gws_core.report.report import Report
from gws_core.report.report_dto import ReportSaveDTO
from gws_core.report.report_service import ReportService
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.r_field.serializable_r_field import SerializableRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view.view_decorator import view
from gws_core.resource.view.view_result import CallViewResult


@resource_decorator("NoteResource", human_name="Note resource",
                    short_description="Resource that contains a rich text that can be exported to a report")
class NoteResource(Resource):

    title: str = StrRField()
    rich_text: RichText = SerializableRField(RichText)

    def __init__(self, title: str = None, rich_text: RichText = None):
        super().__init__()

        if title is not None:
            self.title = title

        if rich_text is not None:
            self.rich_text = rich_text

    def replace_variable(self, variable_name: str, value: str) -> None:
        self.rich_text.replace_variable(variable_name, value)

    def add_paragraph(self, paragraph: str) -> None:
        self.rich_text.add_paragraph(paragraph)

    def add_view(self, resource: Resource, view_method_name: str, config_values: ConfigParamsDict = None,
                 title: str = None, caption: str = None, variable_name: str = None) -> None:
        view_result: CallViewResult = ResourceService.get_and_call_view_on_resource_model(
            resource._model_id, view_method_name, config_values, True)

        self.rich_text.add_resource_views(
            view_result.view_config.to_rich_text_resource_view(title, caption),
            variable_name)

    ############################# Reports #############################

    def export_as_report(self) -> Report:
        """
        Export the note as a report.
        :param report_title: The title of the report
        :return: The report
        """
        if not self.title:
            raise ValueError("The note title is empty")
        report_dto = ReportSaveDTO(title=self.title)
        report: Report = ReportService.create(report_dto)
        return ReportService.update_content(report.id, self.rich_text.get_content())

    ############################# Views #############################

    @view(view_type=RichTextView, human_name="View note", short_description="View note content", default_view=True)
    def view_note(self, config: ConfigParamsDict = None) -> RichTextView:
        return RichTextView(self.rich_text)
