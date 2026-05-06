"""Direct tests for the generic RichTextContentValidator frame and the
form module's registered block rules.

Frame tests (TestRichTextContentValidatorFrame) use a synthetic rule and
plain RichTextBlocks built with arbitrary type strings — no DB writes.

Form-rule tests (TestFormBlockRules) use real Form / FormTemplateVersion
rows via BaseTestCase to exercise reference validation.

Registration footgun guards live in TestRichTextContentValidatorFrame so
they run even without a DB.
"""
import unittest

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.form.form import Form
from gws_core.form.form_dto import CreateFormDTO
from gws_core.form.form_service import FormService
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockTypeStandard
from gws_core.impl.rich_text.block.rich_text_block_form import RichTextBlockForm
from gws_core.impl.rich_text.block.rich_text_block_form_template import (
    RichTextBlockFormTemplate,
)
from gws_core.impl.rich_text.rich_text import (
    RICH_TEXT_CURRENT_VERSION,
    RICH_TEXT_EDITORJS_VERSION,
)
from gws_core.impl.rich_text.rich_text_content_validator import (
    RichTextBlockRule,
    RichTextContentValidator,
    RichTextHostContext,
)
from gws_core.impl.rich_text.rich_text_types import RichTextBlock, RichTextDTO
from gws_core.test.base_test_case import BaseTestCase


def _name_specs() -> ConfigSpecs:
    return ConfigSpecs({"name": StrParam(human_name="name", optional=True)})


def _empty_dto(blocks: list[RichTextBlock]) -> RichTextDTO:
    return RichTextDTO(
        blocks=blocks,
        version=RICH_TEXT_CURRENT_VERSION,
        editorVersion=RICH_TEXT_EDITORJS_VERSION,
    )


def _raw_block(type_: str, id_: str, data: dict | None = None) -> RichTextBlock:
    return RichTextBlock(id=id_, type=type_, data=data or {})


_TEST_BLOCK_TYPE = "test.synthetic_block"


class _RecordingRule(RichTextBlockRule):
    """Synthetic rule used in frame tests. Records every call and lets
    each test configure allowed contexts and an optional raise."""

    def __init__(
        self,
        contexts: set[RichTextHostContext],
        raise_on_validate: bool = False,
    ) -> None:
        self.contexts = contexts
        self.raise_on_validate = raise_on_validate
        self.validated_block_ids: list[str] = []

    @property
    def block_type(self) -> str:
        return _TEST_BLOCK_TYPE

    def allowed_contexts(self) -> set[RichTextHostContext]:
        return self.contexts

    def validate_new_block(self, block: RichTextBlock) -> None:
        self.validated_block_ids.append(block.id)
        if self.raise_on_validate:
            raise BadRequestException("synthetic rule rejected the block")


class TestRichTextContentValidatorFrame(unittest.TestCase):
    """Frame-level tests: walking, dispatch, gating, newly-introduced
    semantics, edge cases, registration. No DB."""

    def tearDown(self) -> None:
        # Always clean up the synthetic rule so other test classes don't
        # see it.
        RichTextContentValidator.unregister(_TEST_BLOCK_TYPE)

    # ---------------- Pass-through ----------------

    def test_unknown_block_type_passes_through(self):
        # Plain paragraphs / unknown block types have no registered rule;
        # validator must accept them.
        new_content = _empty_dto([_raw_block("paragraph", "1")])
        # Should not raise.
        RichTextContentValidator.validate_for_note(new_content, None)
        RichTextContentValidator.validate_for_note_template(new_content, None)

    def test_empty_new_content_is_accepted(self):
        RichTextContentValidator.validate_for_note(_empty_dto([]), None)

    def test_old_content_none_treats_all_blocks_as_new(self):
        rule = _RecordingRule({RichTextHostContext.NOTE})
        RichTextContentValidator.register(rule)

        new_content = _empty_dto(
            [_raw_block(_TEST_BLOCK_TYPE, "a"), _raw_block(_TEST_BLOCK_TYPE, "b")]
        )
        RichTextContentValidator.validate_for_note(new_content, None)

        self.assertEqual(rule.validated_block_ids, ["a", "b"])

    # ---------------- Context gating ----------------

    def test_block_forbidden_in_host_context_raises(self):
        # Rule allows NOTE_TEMPLATE only.
        RichTextContentValidator.register(
            _RecordingRule({RichTextHostContext.NOTE_TEMPLATE})
        )
        new_content = _empty_dto([_raw_block(_TEST_BLOCK_TYPE, "a")])
        with self.assertRaises(BadRequestException):
            RichTextContentValidator.validate_for_note(new_content, None)

    def test_block_allowed_in_host_context_passes_gating(self):
        rule = _RecordingRule({RichTextHostContext.NOTE})
        RichTextContentValidator.register(rule)
        new_content = _empty_dto([_raw_block(_TEST_BLOCK_TYPE, "a")])
        RichTextContentValidator.validate_for_note(new_content, None)
        # Reference hook fired exactly once.
        self.assertEqual(rule.validated_block_ids, ["a"])

    def test_rule_with_all_contexts_only_validates_references(self):
        rule = _RecordingRule(
            {RichTextHostContext.NOTE, RichTextHostContext.NOTE_TEMPLATE}
        )
        RichTextContentValidator.register(rule)
        new_content = _empty_dto([_raw_block(_TEST_BLOCK_TYPE, "a")])
        # Both contexts pass.
        RichTextContentValidator.validate_for_note(new_content, None)
        RichTextContentValidator.validate_for_note_template(new_content, None)
        self.assertEqual(rule.validated_block_ids, ["a", "a"])

    # ---------------- "Newly introduced" gating ----------------

    def test_existing_block_id_skips_reference_check(self):
        rule = _RecordingRule({RichTextHostContext.NOTE})
        RichTextContentValidator.register(rule)
        block = _raw_block(_TEST_BLOCK_TYPE, "stable")
        old = _empty_dto([block])
        new = _empty_dto([block])
        RichTextContentValidator.validate_for_note(new, old)
        # Block was not newly introduced, so the hook never fired —
        # reference rot is tolerated.
        self.assertEqual(rule.validated_block_ids, [])

    def test_new_block_id_triggers_reference_check(self):
        rule = _RecordingRule({RichTextHostContext.NOTE})
        RichTextContentValidator.register(rule)
        old = _empty_dto([_raw_block(_TEST_BLOCK_TYPE, "old")])
        new = _empty_dto(
            [_raw_block(_TEST_BLOCK_TYPE, "old"), _raw_block(_TEST_BLOCK_TYPE, "new")]
        )
        RichTextContentValidator.validate_for_note(new, old)
        # Only the new block id triggered the hook.
        self.assertEqual(rule.validated_block_ids, ["new"])

    def test_new_block_with_failing_reference_raises(self):
        RichTextContentValidator.register(
            _RecordingRule(
                {RichTextHostContext.NOTE}, raise_on_validate=True
            )
        )
        new = _empty_dto([_raw_block(_TEST_BLOCK_TYPE, "x")])
        with self.assertRaises(BadRequestException):
            RichTextContentValidator.validate_for_note(new, None)

    def test_existing_block_with_now_invalid_reference_does_not_raise(self):
        # Same id present in old and new; the rule would reject if
        # called, but the frame must not call it.
        RichTextContentValidator.register(
            _RecordingRule(
                {RichTextHostContext.NOTE}, raise_on_validate=True
            )
        )
        block = _raw_block(_TEST_BLOCK_TYPE, "x")
        RichTextContentValidator.validate_for_note(
            _empty_dto([block]), _empty_dto([block])
        )

    # ---------------- Registration ----------------

    def test_form_block_rule_is_registered_at_package_load(self):
        # Footgun guard: the form module's side-effect import must have
        # registered both rules. Failing this test means the new
        # validator silently allows everything.
        self.assertIsNotNone(
            RichTextContentValidator.get_rule(RichTextBlockTypeStandard.FORM)
        )
        self.assertIsNotNone(
            RichTextContentValidator.get_rule(
                RichTextBlockTypeStandard.FORM_TEMPLATE
            )
        )

    def test_register_replaces_existing_rule(self):
        first = _RecordingRule({RichTextHostContext.NOTE})
        second = _RecordingRule({RichTextHostContext.NOTE})
        RichTextContentValidator.register(first)
        RichTextContentValidator.register(second)
        self.assertIs(
            RichTextContentValidator.get_rule(_TEST_BLOCK_TYPE), second
        )

    def test_unregister_drops_rule(self):
        RichTextContentValidator.register(
            _RecordingRule({RichTextHostContext.NOTE})
        )
        self.assertIsNotNone(
            RichTextContentValidator.get_rule(_TEST_BLOCK_TYPE)
        )
        RichTextContentValidator.unregister(_TEST_BLOCK_TYPE)
        self.assertIsNone(
            RichTextContentValidator.get_rule(_TEST_BLOCK_TYPE)
        )

    def test_unregister_unknown_type_is_noop(self):
        # Should not raise.
        RichTextContentValidator.unregister("never.registered")


class TestFormBlockRules(BaseTestCase):
    """Reference-validity tests for the form module's rules. Needs DB
    rows for Form / FormTemplateVersion."""

    # ---------------- FormBlockRule ----------------

    def test_form_block_rejected_in_note_template(self):
        form = self._make_form()
        new = _empty_dto(
            [
                RichTextBlock.from_data(
                    RichTextBlockForm(
                        form_id=form.id, is_owner=False, display_name=None
                    )
                )
            ]
        )
        with self.assertRaises(BadRequestException):
            RichTextContentValidator.validate_for_note_template(new, None)

    def test_form_block_with_unknown_form_id_raises(self):
        new = _empty_dto(
            [
                RichTextBlock.from_data(
                    RichTextBlockForm(
                        form_id="not-a-real-form-id",
                        is_owner=False,
                        display_name=None,
                    )
                )
            ]
        )
        with self.assertRaises(BadRequestException) as ctx:
            RichTextContentValidator.validate_for_note(new, None)
        self.assertIn("not-a-real-form-id", str(ctx.exception))

    def test_form_block_with_known_form_id_passes(self):
        form = self._make_form()
        new = _empty_dto(
            [
                RichTextBlock.from_data(
                    RichTextBlockForm(
                        form_id=form.id, is_owner=False, display_name=None
                    )
                )
            ]
        )
        RichTextContentValidator.validate_for_note(new, None)

    # ---------------- FormTemplateBlockRule ----------------

    def test_form_template_block_rejected_in_note(self):
        version = self._published_version("FT")
        new = _empty_dto(
            [
                RichTextBlock.from_data(
                    RichTextBlockFormTemplate(
                        form_template_id=version.template_id,
                        form_template_version_id=version.id,
                        display_name=None,
                    )
                )
            ]
        )
        with self.assertRaises(BadRequestException):
            RichTextContentValidator.validate_for_note(new, None)

    def test_form_template_block_with_unknown_version_raises(self):
        new = _empty_dto(
            [
                RichTextBlock.from_data(
                    RichTextBlockFormTemplate(
                        form_template_id="any",
                        form_template_version_id="not-a-real-version-id",
                        display_name=None,
                    )
                )
            ]
        )
        with self.assertRaises(BadRequestException) as ctx:
            RichTextContentValidator.validate_for_note_template(new, None)
        self.assertIn("not-a-real-version-id", str(ctx.exception))

    def test_form_template_block_with_archived_version_raises(self):
        version = self._published_version("FT")
        archived = FormTemplateService.archive_version(
            version.template_id, version.id
        )
        new = _empty_dto(
            [
                RichTextBlock.from_data(
                    RichTextBlockFormTemplate(
                        form_template_id=archived.template_id,
                        form_template_version_id=archived.id,
                        display_name=None,
                    )
                )
            ]
        )
        with self.assertRaises(BadRequestException) as ctx:
            RichTextContentValidator.validate_for_note_template(new, None)
        self.assertIn("PUBLISHED", str(ctx.exception))

    def test_form_template_block_with_mismatched_template_id_raises(self):
        v1 = self._published_version("F1")
        v2 = self._published_version("F2")
        # Pin v1 but lie about the template family.
        new = _empty_dto(
            [
                RichTextBlock.from_data(
                    RichTextBlockFormTemplate(
                        form_template_id=v2.template_id,  # mismatch
                        form_template_version_id=v1.id,
                        display_name=None,
                    )
                )
            ]
        )
        with self.assertRaises(BadRequestException) as ctx:
            RichTextContentValidator.validate_for_note_template(new, None)
        self.assertIn("does not match", str(ctx.exception))

    def test_form_template_block_with_published_version_passes(self):
        version = self._published_version("FT")
        new = _empty_dto(
            [
                RichTextBlock.from_data(
                    RichTextBlockFormTemplate(
                        form_template_id=version.template_id,
                        form_template_version_id=version.id,
                        display_name=None,
                    )
                )
            ]
        )
        RichTextContentValidator.validate_for_note_template(new, None)

    # ---------------- Helpers ----------------

    def _published_version(self, name: str) -> FormTemplateVersion:
        template = FormTemplateService.create(CreateFormTemplateDTO(name=name))
        draft = (
            FormTemplateVersion.select()
            .where(
                (FormTemplateVersion.template == template)
                & (FormTemplateVersion.status == FormTemplateVersionStatus.DRAFT)
            )
            .get()
        )
        draft.update_specs(_name_specs())
        return FormTemplateService.publish_version(template.id, draft.id)

    def _make_form(self) -> Form:
        version = self._published_version("Demo")
        return FormService.create(CreateFormDTO(template_version_id=version.id))
