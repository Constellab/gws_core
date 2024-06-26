

from typing import Any

from gws_core.config.config_types import ConfigParamsDict
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import \
    RichTextParagraphHeaderLevel
from gws_core.impl.rich_text.rich_text_view import RichTextView
from gws_core.model.typing_style import TypingStyle
from gws_core.report.report import Report
from gws_core.report.report_dto import ReportSaveDTO
from gws_core.report.report_service import ReportService
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.r_field.serializable_r_field import SerializableRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view.view_decorator import view
from gws_core.resource.view.view_helper import ViewHelper
from gws_core.resource.view.view_result import CallViewResult


@resource_decorator("ENoteResource", human_name="E-note resource",
                    short_description="Resource that contains a rich text that can be exported to a report",
                    style=TypingStyle.material_icon("sticky_note_2", background_color="#f6f193"),)
class ENoteResource(Resource):

    title: str = StrRField()
    rich_text: RichText = SerializableRField(RichText)

    def __init__(self, title: str = None, rich_text: RichText = None):
        super().__init__()

        if title is not None:
            self.title = title

        if rich_text is not None:
            self.rich_text = rich_text

    def set_parameter(self, parameter_name: str, value: Any) -> None:
        """
        Set the value of a parameter.

        :param parameter_name: parameter name
        :type parameter_name: str
        :param value: value of the parameter. This is convert to str
        :type value: Any
        """
        self.rich_text.set_parameter(parameter_name, str(value))

    def add_paragraph(self, paragraph: str) -> None:
        """
        Add a paragraph to the e-note content.

        :param paragraph: paragraph to add
        :type paragraph: str
        """
        self.rich_text.add_paragraph(paragraph)

    def add_header(self, header: str, level: RichTextParagraphHeaderLevel) -> None:
        """
        Add a header to the e-note content.

        :param header: header to add
        :type header: str
        :param level: header level
        :type level: RichTextParagraphHeaderLevel
        """
        self.rich_text.add_header(header, level)

    def append_enote(self, enote: "ENoteResource") -> None:
        """Append the content of another e-note at the end of the e-note content.

        :param enote: e-note to append
        :type enote: ENoteResource
        """
        self.append_rich_text(enote.rich_text)

    def append_rich_text(self, rich_text: RichText) -> None:
        """Append rich text at the end of the e-note content.

        :param rich_text: rich text to append
        :type rich_text: RichText
        """
        self.rich_text.append_rich_text(rich_text)

    def add_default_view(self, resource: Resource,
                         title: str = None, caption: str = None,
                         parameter_name: str = None) -> None:
        """Add a default view to the e-note content.

        :param resource: resource to call the view on
        :type resource: Resource
        :param title: view title, defaults to None
        :type title: str, optional
        :param caption: view caption, defaults to None
        :type caption: str, optional
        :param parameter_name: if provided, the view replace the provided variable.
                            if not, the view is append at the end of the enote, defaults to None
        :type parameter_name: str, optional
        """
        self.add_view(resource, ViewHelper.DEFAULT_VIEW_NAME, None,
                      title, caption, parameter_name)

    def add_view(self, resource: Resource, view_method_name: str, config_values: ConfigParamsDict = None,
                 title: str = None, caption: str = None, parameter_name: str = None) -> None:
        """Add a view to the e-note content.
        To get the information of the views, once you opened the view in the application, you can
        click on View settings > Show view configuration

        :param resource: resource to call the view on
        :type resource: Resource
        :param view_method_name: name of the view method to call. View settings > Show view configuration.
        :type view_method_name: str
        :param config_values: config values for the views. Access it from View settings > Show view configuration., defaults to None
        :type config_values: ConfigParamsDict, optional
        :param title: view title, defaults to None
        :type title: str, optional
        :param caption: view caption, defaults to None
        :type caption: str, optional
        :param parameter_name: if provided, the view replace the provided parameter.
                            if not, the view is append at the end of the enote, defaults to None
        :type parameter_name: str, optional
        """
        view_result: CallViewResult = ResourceService.get_and_call_view_on_resource_model(
            resource._model_id, view_method_name, config_values, True)

        self.rich_text.add_resource_views(
            view_result.view_config.to_rich_text_resource_view(title, caption),
            parameter_name)

    ############################# Reports #############################

    def export_as_report(self) -> Report:
        """
        Export the note as a report.
        :param report_title: The title of the report
        :return: The report
        """
        if not self.title:
            raise ValueError("The e-note title is empty")
        report_dto = ReportSaveDTO(title=self.title)
        report: Report = ReportService.create(report_dto)
        return ReportService.update_content(report.id, self.rich_text.get_content())

    ############################# Views #############################

    @view(view_type=RichTextView, human_name="View e-note", short_description="View e-note content", default_view=True)
    def view_enote(self, config: ConfigParamsDict = None) -> RichTextView:
        return RichTextView(self.title, self.rich_text)
