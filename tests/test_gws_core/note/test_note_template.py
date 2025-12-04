from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.note_template.note_template_service import NoteTemplateService
from gws_core.test.base_test_case import BaseTestCase


# test_note_template
class TestNoteTemplate(BaseTestCase):
    def test_create_empty(self):
        note_template = NoteTemplateService.create_empty("title")
        self.assertEqual(note_template.title, "title")
        self.assertIsInstance(note_template.content, RichTextDTO)
        self.assertEqual(note_template.content.blocks, [])
