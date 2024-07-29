

from gws_core.config.config_types import ConfigParamsDict
from gws_core.document_template.document_template import DocumentTemplate
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextObjectType
from gws_core.impl.rich_text.rich_text_view import RichTextView
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.view.view_decorator import view


@resource_decorator("DocumentTemplateResource", human_name="Document template resource",
                    short_description="Document template resource",
                    style=TypingStyle.material_icon("document_template", background_color="#735f32"))
class DocumentTemplateResource(Resource):

    document_template_id: str = StrRField()

    _document_template: DocumentTemplate = None
    _content: RichText = None

    def __init__(self, document_template_id: str = None):
        super().__init__()
        self.document_template_id = document_template_id

    def get_content(self) -> RichText:
        if self._content is None:
            self._content = self.get_document_template().get_content_as_rich_text()
        return self._content

    def get_document_template(self) -> DocumentTemplate:
        if self._document_template is None:
            self._document_template = DocumentTemplate.get_by_id_and_check(self.document_template_id)
        return self._document_template

    @view(view_type=RichTextView, human_name="View document template",
          default_view=True)
    def view_document_template(self, config: ConfigParamsDict = None) -> RichTextView:
        return RichTextView(self.get_document_template().title,
                            self.get_content(),
                            object_type=RichTextObjectType.DOCUMENT_TEMPLATE,
                            object_id=self.document_template_id)
