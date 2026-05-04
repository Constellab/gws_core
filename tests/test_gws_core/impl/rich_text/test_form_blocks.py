"""Pure block-level tests for the Phase 6 FORM_TEMPLATE / FORM blocks."""

from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockTypeStandard
from gws_core.impl.rich_text.block.rich_text_block_form import RichTextBlockForm
from gws_core.impl.rich_text.block.rich_text_block_form_template import (
    RichTextBlockFormTemplate,
)
from gws_core.impl.rich_text.rich_text_types import RichTextBlock
from gws_core.test.base_test_case import BaseTestCase


class TestFormBlocks(BaseTestCase):

    # ---------------- RichTextBlockFormTemplate ---------------- #

    def test_form_template_block_round_trip(self):
        data = RichTextBlockFormTemplate(
            form_template_id="tpl-1",
            form_template_version_id="ver-1",
            display_name="Sample collection",
        )
        round_tripped = RichTextBlockFormTemplate.from_json(data.to_json_dict())
        self.assertEqual(round_tripped.form_template_id, "tpl-1")
        self.assertEqual(round_tripped.form_template_version_id, "ver-1")
        self.assertEqual(round_tripped.display_name, "Sample collection")

    def test_form_template_block_display_name_optional(self):
        data = RichTextBlockFormTemplate(
            form_template_id="tpl-1",
            form_template_version_id="ver-1",
        )
        self.assertIsNone(data.display_name)

    def test_form_template_block_to_markdown(self):
        with_name = RichTextBlockFormTemplate(
            form_template_id="tpl-1",
            form_template_version_id="ver-1",
            display_name="Sample collection",
        )
        self.assertIn("Sample collection", with_name.to_markdown())

        without_name = RichTextBlockFormTemplate(
            form_template_id="tpl-1",
            form_template_version_id="ver-1",
        )
        self.assertIn("tpl-1", without_name.to_markdown())

    def test_form_template_block_dispatches_via_get_data(self):
        data = RichTextBlockFormTemplate(
            form_template_id="tpl-1",
            form_template_version_id="ver-1",
        )
        block = RichTextBlock.from_data(data)
        self.assertEqual(block.type, "formTemplate")
        resolved = block.get_data()
        self.assertIsInstance(resolved, RichTextBlockFormTemplate)
        self.assertEqual(resolved.form_template_id, "tpl-1")

    # ---------------- RichTextBlockForm ---------------- #

    def test_form_block_round_trip(self):
        data = RichTextBlockForm(
            form_id="form-1",
            is_owner=True,
            display_name="My form",
        )
        round_tripped = RichTextBlockForm.from_json(data.to_json_dict())
        self.assertEqual(round_tripped.form_id, "form-1")
        self.assertTrue(round_tripped.is_owner)
        self.assertEqual(round_tripped.display_name, "My form")

    def test_form_block_is_owner_required(self):
        # is_owner has no default — both true and false must be explicit.
        owner = RichTextBlockForm(form_id="f", is_owner=True)
        ref = RichTextBlockForm(form_id="f", is_owner=False)
        self.assertTrue(owner.is_owner)
        self.assertFalse(ref.is_owner)

    def test_form_block_to_markdown(self):
        with_name = RichTextBlockForm(
            form_id="form-1", is_owner=False, display_name="My form"
        )
        self.assertIn("My form", with_name.to_markdown())

        without_name = RichTextBlockForm(form_id="form-1", is_owner=True)
        self.assertIn("form-1", without_name.to_markdown())

    def test_form_block_dispatches_via_get_data(self):
        data = RichTextBlockForm(form_id="form-1", is_owner=True)
        block = RichTextBlock.from_data(data)
        self.assertEqual(block.type, "form")
        resolved = block.get_data()
        self.assertIsInstance(resolved, RichTextBlockForm)
        self.assertEqual(resolved.form_id, "form-1")
        self.assertTrue(resolved.is_owner)

    # ---------------- enum registration ---------------- #

    def test_enum_entries_are_standard_types(self):
        self.assertTrue(RichTextBlockTypeStandard.is_standard_type("formTemplate"))
        self.assertTrue(RichTextBlockTypeStandard.is_standard_type("form"))
        self.assertEqual(RichTextBlockTypeStandard.FORM.value, "form")
        self.assertEqual(RichTextBlockTypeStandard.FORM_TEMPLATE.value, "formTemplate")
