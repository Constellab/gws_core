from gws_core.config.config_params import ConfigParamsDict
from gws_core.impl.note_resource.note_resource import NoteResource
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextObjectType
from gws_core.impl.rich_text.rich_text_view import RichTextView
from gws_core.model.typing_style import TypingStyle
from gws_core.note_template.note_template import NoteTemplate
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.view.view_decorator import view


@resource_decorator(
    "NoteTemplateResource",
    human_name="Note template resource",
    short_description="Note template resource",
    style=TypingStyle.material_icon("note_template", background_color="#735f32"),
)
class NoteTemplateResource(Resource):
    note_template_id: str = StrRField()

    _note_template: NoteTemplate = None
    _content: RichText = None

    def __init__(self, note_template_id: str = None):
        super().__init__()
        self.note_template_id = note_template_id

    def get_content(self) -> RichText:
        if self._content is None:
            self._content = self.get_note_template().get_content_as_rich_text()
        return self._content

    def get_note_template(self) -> NoteTemplate:
        if self._note_template is None:
            self._note_template = NoteTemplate.get_by_id_and_check(self.note_template_id)
        return self._note_template

    def generate_note_resource(self) -> NoteResource:
        return NoteResource.from_note_template(self.get_note_template())

    @view(view_type=RichTextView, human_name="View note template", default_view=True)
    def view_note_template(self, config: ConfigParamsDict = None) -> RichTextView:
        return RichTextView(
            self.get_note_template().title,
            self.get_content(),
            object_type=RichTextObjectType.NOTE_TEMPLATE,
            object_id=self.note_template_id,
        )
