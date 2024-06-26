

from typing import Any

from PIL import Image

from gws_core.config.config_types import ConfigParamsDict
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.file.file import File
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_file_service import RichTextFileService
from gws_core.impl.rich_text.rich_text_types import (
    RichTextBlock, RichTextBlockType, RichTextFigureData,
    RichTextParagraphHeaderLevel)
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
from gws_core.resource.resource_set.resource_set import ResourceSet
from gws_core.resource.view.view_decorator import view
from gws_core.resource.view.view_helper import ViewHelper
from gws_core.resource.view.view_result import CallViewResult


@resource_decorator("ENoteResource", human_name="E-note resource",
                    short_description="Resource that contains a rich text that can be exported to a report",
                    style=TypingStyle.material_icon("sticky_note_2", background_color="#f6f193"),)
class ENoteResource(ResourceSet):

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

    def add_blank_line(self) -> None:
        """Add a blank line to the e-note content."""
        self.rich_text.add_paragraph('')

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
        """Append the content of another e-note at the end of this e-note content.

        :param enote: e-note to append
        :type enote: ENoteResource
        """
        for block in enote.rich_text.get_blocks():
            if block.type == RichTextBlockType.FIGURE:
                # add the figure manually (including the resource)
                self.add_figure_file(enote.get_figure(block.data['filename']),
                                     title=block.data['title'], caption=block.data['caption'],
                                     create_new_resource=False)

            else:
                self.rich_text.append_block(block)

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

    ########################################################### FIGURE ###########################################################

    # TODO : gérer les images qui sont dans un template puis utiliser dans une enote
    def add_figure(self, image_path: str, title: str = None, caption: str = None,
                   parameter_name: str = None) -> None:
        file = File(image_path)

        self.add_figure_file(file, title, caption, parameter_name, create_new_resource=True)

    def add_figure_file(self, file: File, title: str = None, caption: str = None,
                        parameter_name: str = None, create_new_resource: bool = True) -> None:

        if not isinstance(file, File):
            raise ValueError("The file must be a File object")

        if not file.is_image():
            raise ValueError("The file must be an image")

        if create_new_resource:
            file.name = (title or f"file_{len(self)}") + "." + file.extension

        image = Image.open(file.path)

        filename = f"{StringHelper.generate_uuid()}_{str(DateHelper.now_utc_as_milliseconds())}.{file.extension}"
        figure_data: RichTextFigureData = {
            "filename": filename,
            "width": image.size[0],
            "height": image.size[1],
            "naturalWidth": image.size[0],
            "naturalHeight": image.size[1],
            "title": title,
            "caption": caption,
        }

        self.rich_text.add_figure(figure_data, parameter_name=parameter_name)

        self.add_resource(file, filename, create_new_resource=create_new_resource)

    def get_figure(self, filename: str) -> File:
        """
        Get the figure of the enote as a File  resource.

        :param filename: filename of the figure
        :type filename: str
        :raises ValueError: The resource must be a File object
        :return: the figure as a File resource
        :rtype: File
        """
        file: Resource = self.get_resource(filename)

        if not isinstance(file, File):
            raise ValueError("The resource must be a File object")

        return file

    def get_figure_path(self, filename: str) -> str:
        """
        Get the path of the figure file.

        :param filename: filename of the figure
        :type filename: str
        :return: path of the figure file
        :rtype: str
        """
        return self.get_figure(filename).path

    # def add_view_2(self, view_: View, view_config_values: ConfigParamsDict = None,
    #                title: str = None, caption: str = None, parameter_name: str = None) -> None:
    #     view_data: RichTextResourceViewData = {
    #         "id": StringHelper.generate_uuid() + "_" + str(DateHelper.now_utc_as_milliseconds()),  # generate a unique id
    #         "view_config_id": None,
    #         "resource_id": None,
    #         "experiment_id": None,
    #         "view_method_name": None,
    #         "view_config": self.get_config_values(),
    #         "title": title or self.title,
    #         "caption": caption or "",
    #     }
    #     self.rich_text.add_resource_views(
    #         view_result.view_config.to_rich_text_resource_view(title, caption),
    #         parameter_name)

    ############################# Others #############################
    def append_block(self, block: RichTextBlock) -> int:
        """
        Append a block to the enote

        :param block: block to add
        :type block: RichTextBlock
        :return: index of the new block
        :rtype: int
        """
        return self.rich_text.append_block(block)

    ############################# Reports #############################

    def append_report_rich_text(self, rich_text: RichText) -> None:
        """
        Append a rich text (that comes from a report, report template or RichTextParam) to the e-note.

        :param rich_text: rich text to append to the e-note (from a report, report template or RichTextParam)
        :type rich_text: RichText
        :return: the e-note
        :rtype: _type_
        """
        # add the block 1 by 1 to the enote
        for block in rich_text.get_blocks():
            # specific case for the figure
            if block.type == RichTextBlockType.FIGURE:

                # get the path of the figure, to add the figure to enote
                filename = RichTextFileService.get_file_path(block.data['filename'])
                # add the figure manually
                self.add_figure(filename, block.data['title'], block.data['caption'])
            else:
                self.append_block(block)

    def export_as_report(self) -> Report:
        """
        Export the note as a report. The report is automatically saved in the database.
        :param report_title: The title of the report
        :return: The report
        """
        if not self.title:
            raise ValueError("The e-note title is empty")
        report_dto = ReportSaveDTO(title=self.title)
        report: Report = ReportService.create(report_dto)

        report_rich_text = self.export_as_report_rich_text()

        # save the content to the report
        return ReportService.update_content(report.id, report_rich_text.get_content())

    def export_as_report_rich_text(self) -> RichText:
        """
        Convert the enote rich text to a report rich text.

        :return: the report rich text
        :rtype: RichText
        """
        report_rich_text = RichText()

        # add the block 1 by 1 to the report
        for block in self.rich_text.get_blocks():
            # specific case for the figure
            if block.type == RichTextBlockType.FIGURE:
                figure_file = self.get_figure(block.data['filename'])

                image: Image.Image = None
                try:
                    image = Image.open(figure_file.path)
                except Exception:
                    raise Exception(f'The file {figure_file.path} is not an image')

                # add the figure to report storage
                result = RichTextFileService.save_image(image, figure_file.extension)

                # add the figure manually
                figure_data: RichTextFigureData = {
                    "filename": result.filename,
                    "width": result.width,
                    "height": result.height,
                    "naturalWidth": result.width,
                    "naturalHeight": result.height,
                    "title": block.data['title'],
                    "caption": block.data['caption'],
                }
                report_rich_text.add_figure(figure_data)
            else:
                report_rich_text.append_block(block)

        return report_rich_text

    ############################# Views #############################

    @view(view_type=RichTextView, human_name="View e-note", short_description="View e-note content", default_view=True)
    def view_enote(self, config: ConfigParamsDict = None) -> RichTextView:
        return RichTextView(self.title, self.rich_text)
