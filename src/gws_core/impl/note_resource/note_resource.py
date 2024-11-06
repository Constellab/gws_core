

from typing import Any, List

from PIL import Image

from gws_core.config.config_types import ConfigParamsDict
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_file_service import RichTextFileService
from gws_core.impl.rich_text.rich_text_types import (
    RichTextBlock, RichTextBlockType, RichTextFigureData, RichTextFileData,
    RichTextNoteResourceViewData, RichTextObjectType,
    RichTextParagraphHeaderLevel, RichTextResourceViewData,
    RichTextViewFileData)
from gws_core.impl.rich_text.rich_text_view import RichTextView
from gws_core.model.typing_style import TypingStyle
from gws_core.note.note import Note
from gws_core.note.note_dto import NoteSaveDTO
from gws_core.note.note_service import NoteService
from gws_core.note_template.note_template import NoteTemplate
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.r_field.serializable_r_field import SerializableRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.resource_set.resource_set import ResourceSet
from gws_core.resource.view.view import View
from gws_core.resource.view.view_decorator import view
from gws_core.resource.view.view_dto import CallViewResultDTO
from gws_core.resource.view.view_helper import ViewHelper
from gws_core.resource.view.view_resource import ViewResource
from gws_core.resource.view.view_result import CallViewResult
from gws_core.resource.view.view_runner import ViewRunner


@resource_decorator("NoteResource", human_name="Note resource",
                    short_description="Resource that contains a rich text that can be exported to a lab note",
                    style=TypingStyle.material_icon("sticky_note_2", background_color="#f6f193"),)
class NoteResource(ResourceSet):

    title: str = StrRField()
    _rich_text: RichText = SerializableRField(RichText)

    def __init__(self, title: str = None):
        super().__init__()

        if title is not None:
            self.title = title

        self._rich_text = RichText()

    def set_parameter(self, parameter_name: str, value: Any) -> None:
        """
        Set the value of a parameter.

        :param parameter_name: parameter name
        :type parameter_name: str
        :param value: value of the parameter. This is convert to str
        :type value: Any
        """
        self._rich_text.set_parameter(parameter_name, str(value))

    def add_paragraph(self, paragraph: str) -> None:
        """
        Add a paragraph to the note resource content.

        :param paragraph: paragraph to add
        :type paragraph: str
        """
        self._rich_text.add_paragraph(paragraph)

    def add_blank_line(self) -> None:
        """Add a blank line to the note resource content."""
        self._rich_text.add_paragraph('')

    def add_header(self, header: str, level: RichTextParagraphHeaderLevel) -> None:
        """
        Add a header to the note resource content.

        :param header: header to add
        :type header: str
        :param level: header level
        :type level: RichTextParagraphHeaderLevel
        """
        self._rich_text.add_header(header, level)

    ########################################################### VIEW ###########################################################

    def add_default_view_from_resource(self, resource: Resource,
                                       title: str = None, caption: str = None,
                                       parameter_name: str = None,
                                       create_new_resource: bool = False) -> None:
        """Add a default view to the note resource content. This method is reponsible for generating the view of the input resource and the input resource
        will be attached to the NoteResource.

        :param resource: resource to call the view on
        :type resource: Resource
        :param title: view title, defaults to None
        :type title: str, optional
        :param caption: view caption, defaults to None
        :type caption: str, optional
        :param parameter_name: if provided, the view replace the provided variable.
                            if not, the view is append at the end of the note, defaults to None
        :type parameter_name: str, optional
        """
        self.add_view_from_resource(resource, ViewHelper.DEFAULT_VIEW_NAME, None,
                                    title, caption, parameter_name, create_new_resource)

    def add_view_from_resource(self, resource: Resource,
                               view_method_name: str,
                               config_values: ConfigParamsDict = None,
                               title: str = None,
                               caption: str = None,
                               parameter_name: str = None,
                               create_new_resource: bool = False) -> None:
        """Add a view to the note resource content. This method is reponsible for generating the view of the input resource and the input resource
        will be attached to the NoteResource.
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
                            if not, the view is append at the end of the note, defaults to None
        :type parameter_name: str, optional
        """
        # store the resource in the note
        self.add_resource(resource, resource.uid,
                          create_new_resource=create_new_resource)

        self._add_view(resource.uid, view_method_name, config_values, title, caption, parameter_name)

    def add_view(self, view_: View,
                 view_config_values: ConfigParamsDict = None,
                 title: str = None, caption: str = None,
                 parameter_name: str = None) -> None:
        """
        Add a view to the note resource content. In this case the resource is not attached to the NoteResource, the
        view is considered as standalone. This can be useful when you want to add a view of a resource that does not exist in the
        system (manually created resource).

        :param view: view to add
        :type view: View
        :param view_config_values: config value of the view when call to_json_dict, defaults to None
        :type view_config_values: ConfigParamsDict, optional
        :param title: title of the view, defaults to None
        :type title: str, optional
        :param caption: caption of the view, defaults to None
        :type caption: str, optional
        :param parameter_name: if provided, the view replace the provided variable.
                              If not, the view is append at the end of the note, defaults to None
        :type parameter_name: str, optional
        """
        view_resource = ViewResource.from_view(view_, view_config_values)
        self._add_view_resource(view_resource, view_config_values, title, caption, parameter_name)

    def _add_view_resource(self, view_resource: ViewResource,
                           view_config_values: ConfigParamsDict = None,
                           title: str = None, caption: str = None,
                           parameter_name: str = None) -> None:
        """
        Add a view resource to the note resource content.

        :param view: view to add
        :type view: View
        :param view_config_values: config value of the view when call to_json_dict, defaults to None
        :type view_config_values: ConfigParamsDict, optional
        :param title: title of the view, defaults to None
        :type title: str, optional
        :param caption: caption of the view, defaults to None
        :type caption: str, optional
        :param parameter_name: if provided, the view replace the provided variable.
                              If not, the view is append at the end of the note, defaults to None
        :type parameter_name: str, optional
        """
        view_resource.name = title
        self.add_resource(view_resource, view_resource.uid, create_new_resource=True)

        self._add_view(view_resource.uid, ViewHelper.DEFAULT_VIEW_NAME,
                       view_config_values, title, caption, parameter_name)

    def _add_view(self, resource_key: str,
                  view_method_name: str,
                  view_config_values: ConfigParamsDict = None,
                  title: str = None, caption: str = None,
                  parameter_name: str = None) -> None:
        rich_text_view: RichTextNoteResourceViewData = {
            "id": StringHelper.generate_uuid() + "_" + str(DateHelper.now_utc_as_milliseconds()),  # generate a unique id
            "sub_resource_key": resource_key,
            "view_method_name": view_method_name,
            "view_config": view_config_values or {},
            "title": title or "",
            "caption": caption or "",
        }
        self._rich_text.add_note_resource_view(rich_text_view, parameter_name)

    def call_view_on_resource(self, resource_key: str, view_name: str, config: ConfigParamsDict) -> CallViewResultDTO:
        """Call a view method on the resource.

        :param resource_key: key of the resource
        :type resource_key: str
        :return: result of the view method
        :rtype: CallViewResultDTO
        """
        resource = self.get_resource(resource_key)

        view_result: CallViewResult = ResourceService.get_and_call_view_on_resource_model(
            resource.get_model_id(), view_name, config, False)

        return view_result.to_dto()

    ########################################################### FIGURE ###########################################################

    def add_figure_from_path(self, image_path: str, title: str = None, caption: str = None,
                             parameter_name: str = None) -> None:
        """
        Add a figure to the note resource content.

        :param image_path: path of the image file
        :type image_path: str
        :param title: title of the figure, defaults to None
        :type title: str, optional
        :param caption: caption of the figure, defaults to None
        :type caption: str, optional
        :param parameter_name: if provided, the figure replace the provided variable.
                              If not, the figure is append at the end of the note, defaults to None
        :type parameter_name: str, optional
        """
        file = File(image_path)

        self.add_figure_file(file, title, caption, parameter_name, create_new_resource=True)

    def add_figure_file(self, file: File, title: str = None, caption: str = None,
                        parameter_name: str = None, create_new_resource: bool = False) -> None:
        """
        Add a figure to the note resource content.

        :param file: file of the image
        :type file: File
        :param title: title of the figure, defaults to None
        :type title: str, optional
        :param caption: caption of the figure, defaults to None
        :type caption: str, optional
        :param parameter_name: if provided, the figure replace the provided variable.
                                If not, the figure is append at the end of the note, defaults to None
        :type parameter_name: str, optional
        :param create_new_resource: if True, a new resource is created with the file.
                                    If False, the file is used as a resource.
                                    Set False if the File resource already exist ans saved on the lab, defaults to True
        :type create_new_resource: bool, optional
        :raises ValueError: _description_
        :raises ValueError: _description_
        """

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

        self._rich_text.add_figure(figure_data, parameter_name=parameter_name)

        self.add_resource(file, filename, create_new_resource=create_new_resource)

    def get_figure(self, filename: str) -> File:
        """
        Get the figure of the note as a File  resource.

        :param filename: filename of the figure
        :type filename: str
        :raises ValueError: The resource must be a File object
        :return: the figure as a File resource
        :rtype: File
        """
        return self.get_file(filename)

    ########################################################### FILE ###########################################################

    def add_file_from_path(self, file_path: str, parameter_name: str = None) -> None:
        """
        Add a file to the note resource content.

        :param file_path: path of the file
        :type file_path: str
        :param parameter_name: if provided, the file replace the provided variable.
                                If not, the file is append at the end of the note, defaults to None
        :type parameter_name: str, optional
        """

        file = File(file_path)

        self.add_file(file, parameter_name, create_new_resource=True)

    def add_file(self, file: File, parameter_name: str = None,
                 create_new_resource: bool = False) -> None:
        """
        Add a file to the note resource content.

        :param file: file to add
        :type file: File
        :param parameter_name: if provided, the file replace the provided variable.
                                If not, the file is append at the end of the note, defaults to None
        :type parameter_name: str, optional
        :param create_new_resource: if True, a new resource is created with the file.
                                    If False, the file is used as a resource.
                                    Set False if the File resource already exist ans saved on the lab, defaults to True
        :type create_new_resource: bool, optional
        """

        filename = file.get_base_name()

        if self.resource_exists(filename):
            raise ValueError(f"The file {filename} already exists in the note resource")

        self._rich_text.add_file({
            "name": filename,
            "size": file.get_size(),
        }, parameter_name=parameter_name)

        self.add_resource(file, filename, create_new_resource=create_new_resource)

    def get_file(self, filename: str) -> File:
        """
        Get the file of the note as a File resource.

        :param filename: filename of the file
        :type filename: str
        :raises ValueError: The resource must be a File object
        :return: the file as a File resource
        :rtype: File
        """
        file: Resource = self.get_resource(filename)

        if not isinstance(file, File):
            raise ValueError("The resource must be a File object")

        return file

    def get_file_path(self, filename: str) -> str:
        """
        Get the path of the file.

        :param filename: filename of the file
        :type filename: str
        :return: path of the file
        :rtype: str
        """
        return self.get_file(filename).path

    ############################# Block #############################

    def append_block(self, block: RichTextBlock) -> int:
        """
        Append a block to the note

        :param block: block to add
        :type block: RichTextBlock
        :return: index of the new block
        :rtype: int
        """
        return self._rich_text.append_block(block)

    def get_blocks(self) -> List[RichTextBlock]:
        """
        Get the blocks of the note resource

        :return: list of blocks
        :rtype: List[RichTextBlock]
        """
        return self._rich_text.get_blocks()

    def get_blocks_by_type(self, block_type: RichTextBlockType) -> List[RichTextBlock]:
        """
        Get the blocks of the note resource by type

        :param block_type: type of the block
        :type block_type: RichTextBlockType
        :return: list of blocks
        :rtype: List[RichTextBlock]
        """
        return [block for block in self.get_blocks() if block.type == block_type]

    def get_block_at_index(self, index: int) -> RichTextBlock:
        """
        Get the block at the specified index

        :param index: index of the block
        :type index: int
        :return: the block
        :rtype: RichTextBlock
        """
        return self._rich_text.get_block_at_index(index)

    def get_block_by_id(self, block_id: str) -> RichTextBlock:
        """
        Get the block by id

        :param block_id: id of the block
        :type block_id: str
        :return: the block
        :rtype: RichTextBlock
        """
        return self._rich_text.get_block_by_id(block_id)

    def get_block_index_by_id(self, block_id: str) -> int:
        """
        Get the index of the block by id

        :param block_id: id of the block
        :type block_id: str
        :return: index of the block
        :rtype: int
        """
        return self._rich_text.get_block_index_by_id(block_id)

    ############################# Other #############################

    def append_note_resource(self, note: "NoteResource") -> None:
        """Append the content of another note resource at the end of this note resource content.

        :param note: note resource to append
        :type note: NoteResource
        """
        for block in note.get_blocks():
            if block.type == RichTextBlockType.FIGURE:
                # add the figure manually (including the resource)
                figure_data: RichTextFigureData = block.data
                self.add_figure_file(note.get_file(figure_data['filename']),
                                     title=figure_data['title'], caption=figure_data['caption'],
                                     create_new_resource=False)
            elif block.type == RichTextBlockType.FILE:
                # add the file manually (including the resource)
                file_data: RichTextFileData = block.data
                self.add_file(note.get_file(file_data['name']), create_new_resource=False)

            elif block.type == RichTextBlockType.NOTE_RESOURCE_VIEW:
                # add the view manually (including the resource)
                view_data: RichTextNoteResourceViewData = block.data
                self.add_view_from_resource(note.get_resource(view_data['sub_resource_key']),
                                            view_method_name=view_data['view_method_name'],
                                            config_values=view_data['view_config'],
                                            title=view_data['title'],
                                            caption=view_data['caption'],
                                            create_new_resource=False)

            else:
                self._rich_text.append_block(block)

    def append_basic_rich_text(self, rich_text: RichText) -> None:
        """Append a basic rich content to this note resource content.
        It does not support file, figure, or views

        :param rich_text: rich text to append
        :type rich_text: RichText
        """
        # add the block 1 by 1 to the note
        for block in rich_text.get_blocks():
            self.append_block(block)

    def append_advanced_rich_text(self, rich_text: RichText,
                                  object_type: RichTextObjectType,
                                  object_id: str) -> None:
        """
        Append a rich text (that comes from a note or note template) to the note resource.

        :param rich_text: rich text to append to the note resource (from a note or note template)
        :type rich_text: RichText
        :param object_type: type of the object that has the rich text
        :type object_type: RichTextObjectType
        :param object_id: id of the object that has the rich text
        :type object_id: str
        :return: the note resource
        :rtype: _type_
        """
        if object_type == RichTextObjectType.NOTE_RESOURCE:
            raise ValueError("Please use append_note to append an note resource to another note resource")

        # add the block 1 by 1 to the note
        for block in rich_text.get_blocks():
            # specific case for the figure
            if block.type == RichTextBlockType.FIGURE:
                figure_data: RichTextFigureData = block.data

                # get the path of the figure, to add the figure to note
                filename = RichTextFileService.get_object_file_path(object_type, object_id,
                                                                    figure_data['filename'])
                # add the figure manually
                self.add_figure_from_path(filename, figure_data['title'], figure_data['caption'])
            elif block.type == RichTextBlockType.FILE:
                # add the file manually
                file_data: RichTextFileData = block.data
                filename = RichTextFileService.get_object_file_path(object_type, object_id, file_data['name'])
                self.add_file_from_path(filename)
            elif block.type == RichTextBlockType.RESOURCE_VIEW:
                # add the view manually
                view_data: RichTextResourceViewData = block.data
                resource_model = ResourceModel.get_by_id_and_check(view_data['resource_id'])
                self.add_view_from_resource(resource_model.get_resource(),
                                            view_method_name=view_data['view_method_name'],
                                            config_values=view_data['view_config'],
                                            title=view_data['title'],
                                            caption=view_data['caption'],
                                            create_new_resource=False)
            elif block.type == RichTextBlockType.FILE_VIEW:
                # convert the file view to a ViewResource
                file_view_data: RichTextViewFileData = block.data
                view_result = RichTextFileService.get_file_view(object_type, object_id, file_view_data['filename'])

                view_resource = ViewResource.from_view_dto(view_result.view)
                self._add_view_resource(view_resource, view_config_values=None,
                                        title=file_view_data["title"], caption=file_view_data["caption"])

            else:
                self.append_block(block)

    ############################# Notes #############################

    def export_as_lab_note(self, title: str = None) -> Note:
        """
        Export the note as a note. The note is automatically saved in the database.
        :param note_title: The title of the note
        :return: The note
        """
        if not title and not self.title:
            raise ValueError("The note resource title is empty")
        note_dto = NoteSaveDTO(title=title or self.title)
        note: Note = NoteService.create(note_dto)

        note_rich_text = self._export_as_lab_note_rich_text(note.id)

        # save the content to the note
        return NoteService.update_content(note.id, note_rich_text.get_content())

    def _export_as_lab_note_rich_text(self, note_id: str) -> RichText:
        """
        Convert the note rich text to a note rich text.

        :return: the note rich text
        :rtype: RichText
        """
        note_rich_text = RichText()

        # add the block 1 by 1 to the note
        for block in self._rich_text.get_blocks():
            # specific case for the figure
            if block.type == RichTextBlockType.FIGURE:
                # add the figure manually
                figure_data = self._convert_figure_for_lab_note_rich_text(block.data, note_id)
                note_rich_text.add_figure(figure_data)
            elif block.type == RichTextBlockType.FILE:
                # add the file manually
                file_data = self._convert_file_for_lab_note_rich_text(block.data, note_id)
                note_rich_text.add_file(file_data)
            elif block.type == RichTextBlockType.NOTE_RESOURCE_VIEW:
                # add the view manually
                self._add_note_view_to_note_rich_text(block.data, note_rich_text, note_id)
            else:
                note_rich_text.append_block(block)

        return note_rich_text

    def _convert_figure_for_lab_note_rich_text(
            self, note_figure: RichTextFigureData, note_id: str) -> RichTextFigureData:
        """Method to convert a note figure to a note figure. It saves the figure in the note storage.
        """
        figure_file = self.get_file(note_figure['filename'])
        image: Image.Image = None
        try:
            image = Image.open(figure_file.path)
        except Exception:
            raise Exception(f'The file {figure_file.path} is not an image')

        # add the figure to note storage
        result = RichTextFileService.save_image(RichTextObjectType.NOTE, note_id,
                                                image, figure_file.extension)

        # add the figure manually
        return {
            "filename": result.filename,
            "width": result.width,
            "height": result.height,
            "naturalWidth": result.width,
            "naturalHeight": result.height,
            "title": note_figure['title'],
            "caption": note_figure['caption'],
        }

    def _convert_file_for_lab_note_rich_text(
            self, note_file: RichTextFileData, note_id: str) -> RichTextFileData:
        """Method to convert a note figure to a note figure. It saves the figure in the note storage.
        """
        # retrieve the file
        file = self.get_file(note_file['name'])

        # get the file destination for the note
        destination_file_path = RichTextFileService.get_uploaded_file_path(RichTextObjectType.NOTE,
                                                                           note_id,
                                                                           file.get_base_name())

        RichTextFileService.create_object_dir(RichTextObjectType.NOTE, note_id)

        # copy the file to the destination
        FileHelper.copy_file(file.path, destination_file_path)

        # the object is the same as the note
        return note_file

    def _add_note_view_to_note_rich_text(self, note_view: RichTextNoteResourceViewData,
                                         note_rich_text: RichText, note_id: str) -> None:

        # retrieve the resource model from the resource
        resource = self.get_resource(note_view['sub_resource_key'])

        if resource.get_model_id() is not None:
            # add the view manually from the resource and config
            view_data = self._convert_view_for_lab_note_rich_text(note_view)
            note_rich_text.add_resource_view(view_data)
        else:
            # add the view manually from a json file (without the resource)
            view_data_2 = self._convert_file_view_for_lab_note_rich_text(note_view, note_id)
            note_rich_text.add_file_view(view_data_2)

    def _convert_view_for_lab_note_rich_text(self, note_view: RichTextNoteResourceViewData) -> RichTextResourceViewData:
        """Method to convert a note view to a note view.
        """
        # retrieve the resource model from the resource
        resource = self.get_resource(note_view['sub_resource_key'])

        if not resource.get_model_id():
            raise ValueError(
                f"The resource {note_view['sub_resource_key']} of the note resource was not saved on the database.")

        view_result: CallViewResult = ResourceService.get_and_call_view_on_resource_model(
            resource.get_model_id(), note_view['view_method_name'], note_view["view_config"], True)

        return view_result.view_config.to_rich_text_resource_view()

    def _convert_file_view_for_lab_note_rich_text(
            self, note_view: RichTextNoteResourceViewData, note_id: str) -> RichTextViewFileData:

        # retrieve the resource model from the resource
        resource = self.get_resource(note_view['sub_resource_key'])

        view_runner: ViewRunner = ViewRunner(resource, note_view['view_method_name'], note_view["view_config"])

        view_ = view_runner.generate_view()
        # call the view to dict
        view_dto = view_runner.call_view_to_dto()

        view_result = CallViewResult(view_dto,
                                     resource_id=None,
                                     view_config=None,
                                     title=view_.get_title() or resource.name or "View",
                                     view_type=view_dto.type,
                                     style=view_.get_style() or view_runner.get_metadata_style())

        # save the json as a file
        filename = RichTextFileService.save_file_view(RichTextObjectType.NOTE, note_id,
                                                      view_result.to_dto())

        return {
            "id": note_view['id'],
            "filename": filename,
            "title": note_view['title'],
            "caption": note_view['caption'],
        }

    ############################# Views #############################

    @view(view_type=RichTextView, human_name="View note resource", short_description="View note resource content", default_view=True)
    def view_note(self, config: ConfigParamsDict = None) -> RichTextView:
        return RichTextView(self.title, self._rich_text,
                            object_type=RichTextObjectType.NOTE_RESOURCE,
                            object_id=self.get_model_id())

    ############################# Constructors #############################

    @staticmethod
    def from_note_template(note_template: NoteTemplate,
                           title: str = None) -> "NoteResource":
        """Create a note resource from a note template.

        :param note_template: note template to create the note resource from
        :type note_template: NoteTemplate
        :param title: title of the note resource. If none the title of note template is used, defaults to None
        :type title: str, optional
        :return: the note resource
        :rtype: NoteResource
        """
        note = NoteResource()
        rich_text = RichText(note_template.content)
        note.append_advanced_rich_text(rich_text, RichTextObjectType.NOTE_TEMPLATE, note_template.id)
        note.title = title or note_template.title
        return note

    @staticmethod
    def from_note(note: Note,
                  title: str = None) -> "NoteResource":
        """Create a note resource from a note.

        :param note: note to create the note resource from
        :type note: Note
        :param title: title of the note resource. If none the title of note is used, defaults to None
        :type title: str, optional
        :return: the note resource
        :rtype: NoteResource
        """
        note = NoteResource()
        rich_text = RichText(note.content)
        note.append_advanced_rich_text(rich_text, RichTextObjectType.NOTE, note.id)
        note.title = title or note.title
        return note
