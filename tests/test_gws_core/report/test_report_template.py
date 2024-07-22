

from gws_core.document_template.document_template_service import \
    DocumentTemplateService
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.test.base_test_case import BaseTestCase


# test_document_template
class TestDocumentTemplate(BaseTestCase):

    def test_create_empty(self):
        document_template = DocumentTemplateService.create_empty('title')
        self.assertEqual(document_template.title, 'title')
        self.assertIsInstance(document_template.content, RichTextDTO)
        self.assertEqual(document_template.content.blocks, [])
