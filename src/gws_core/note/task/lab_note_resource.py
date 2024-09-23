

from gws_core.config.config_types import ConfigParamsDict
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextObjectType
from gws_core.impl.rich_text.rich_text_view import RichTextView
from gws_core.model.typing_style import TypingStyle
from gws_core.note.note import Note
from gws_core.note.note_service import NoteService
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view.view_decorator import view
from gws_core.resource.view.view_result import CallViewResult


@resource_decorator("LabNoteResource", human_name="Lab note resource", short_description="Lab note resource",
                    style=TypingStyle.material_icon("note", background_color="#735f32"))
class LabNoteResource(Resource):

    note_id: str = StrRField()

    _note: Note = None
    _content: RichText = None

    def __init__(self, note_id: str = None):
        super().__init__()
        self.note_id = note_id

    def get_content(self) -> RichText:
        if self._content is None:
            self._content = self.get_note().get_content_as_rich_text()
        return self._content

    def get_note(self) -> Note:
        if self._note is None:
            self._note = Note.get_by_id_and_check(self.note_id)
        return self._note

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
            resource.get_model_id(), view_method_name, config_values, True)

        rich_text: RichText = self.get_content()
        rich_text.add_resource_view(view_result.view_config.to_rich_text_resource_view(title, caption), variable_name)
        self._content = rich_text

    def update_title(self, title: str) -> None:
        self._note = NoteService.update_title(self.note_id, title)

    def save(self):
        note = NoteService.update_content(self.note_id, self.get_content().get_content())
        self._content = note.get_content_as_rich_text()

    @view(view_type=RichTextView, human_name="View note", short_description="View note content", default_view=True)
    def view_note(self, config: ConfigParamsDict = None) -> RichTextView:
        return RichTextView(self.get_note().title,
                            self.get_content(),
                            object_type=RichTextObjectType.NOTE,
                            object_id=self.note_id)
