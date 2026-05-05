from abc import ABC, abstractmethod
from enum import Enum

from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockTypeStandard
from gws_core.impl.rich_text.rich_text_types import RichTextBlock, RichTextDTO


class RichTextHostContext(Enum):
    """The kind of object whose rich-text content is being validated.

    Block-type rules declare which contexts they accept; the validator
    rejects blocks that appear in a context their rule forbids.
    """
    NOTE = "note"
    NOTE_TEMPLATE = "note_template"


class RichTextBlockRule(ABC):
    """A per-block-type validation rule registered with
    `RichTextContentValidator`.

    Subclass and register via `RichTextContentValidator.register(...)` to
    plug context gating and reference-validity checks for a new block
    type into the generic validator. Modules own their own rules; the
    rich-text core stays unaware of the form module, of any future block
    type, etc.

    Frame responsibilities (handled by the validator, not the rule):

    - Walking new content's blocks.
    - Computing the "newly introduced" set (block ids absent from old content).
    - Dispatching to the rule's hooks.

    Per-rule responsibilities:

    - Declaring which contexts (`NOTE`, `NOTE_TEMPLATE`, …) the block type
      is allowed in.
    - Validating references inside *newly introduced* blocks (existing
      blocks survive even if their target is later archived/deleted —
      the frame handles that gating).
    """

    @property
    @abstractmethod
    def block_type(self) -> RichTextBlockTypeStandard | str:
        """The block type this rule governs."""

    @abstractmethod
    def allowed_contexts(self) -> set[RichTextHostContext]:
        """The set of host contexts this block type is allowed in.

        Returning an empty set is legal but unusual — it means the block
        type cannot appear anywhere this validator runs. Returning all
        contexts means the rule only contributes reference-validity
        checks, not gating.
        """

    def validate_new_block(self, block: RichTextBlock) -> None:
        """Hook called for *newly introduced* blocks of `block_type`.
        Override to validate references (e.g. "the form id exists",
        "the version is PUBLISHED"). Default: no-op.

        Raise `BadRequestException` to reject the content update.
        """
        return


class RichTextContentValidator:
    """Generic validator for rich-text content updates.

    Owns the frame ("walk blocks, dispatch to per-block-type rules,
    enforce host-context gating, only check references for newly
    introduced blocks"). Knows nothing about specific block types; rules
    plug their own logic in via `register(...)`.

    Rules are registered at module import time — typically as side-effect
    imports from `gws_core/__init__.py`, mirroring the event-listener
    pattern. Registering a rule for a block type that already has one
    replaces the prior rule (intentional: makes hot-reloading and tests
    straightforward; in production each block type has exactly one rule).

    Two public entry points wrap the generic `validate(...)` for the
    callers that exist today (`NoteService`, `NoteTemplateService`); both
    reduce to `validate(NEW_CONTENT, OLD_CONTENT, host=...)`.
    """

    _rules: dict[str, RichTextBlockRule] = {}

    # ------------------------------------------------------------------ #
    # Registration
    # ------------------------------------------------------------------ #

    @classmethod
    def register(cls, rule: RichTextBlockRule) -> None:
        """Register (or replace) the rule for a block type."""
        key = cls._block_type_key(rule.block_type)
        cls._rules[key] = rule

    @classmethod
    def unregister(cls, block_type: RichTextBlockTypeStandard | str) -> None:
        """Remove the rule for a block type. No-op if no rule is registered.

        Useful in tests that register a synthetic rule and need to clean
        up afterwards.
        """
        cls._rules.pop(cls._block_type_key(block_type), None)

    @classmethod
    def get_rule(
        cls, block_type: RichTextBlockTypeStandard | str
    ) -> RichTextBlockRule | None:
        return cls._rules.get(cls._block_type_key(block_type))

    @staticmethod
    def _block_type_key(block_type: RichTextBlockTypeStandard | str) -> str:
        if isinstance(block_type, RichTextBlockTypeStandard):
            return block_type.value
        return block_type

    # ------------------------------------------------------------------ #
    # Validation entry points
    # ------------------------------------------------------------------ #

    @classmethod
    def validate_for_note(
        cls,
        new_content: RichTextDTO,
        old_content: RichTextDTO | None = None,
    ) -> None:
        cls.validate(new_content, old_content, host=RichTextHostContext.NOTE)

    @classmethod
    def validate_for_note_template(
        cls,
        new_content: RichTextDTO,
        old_content: RichTextDTO | None = None,
    ) -> None:
        cls.validate(
            new_content, old_content, host=RichTextHostContext.NOTE_TEMPLATE
        )

    @classmethod
    def validate(
        cls,
        new_content: RichTextDTO,
        old_content: RichTextDTO | None,
        host: RichTextHostContext,
    ) -> None:
        """Walk new content; reject blocks whose registered rule forbids
        them in `host`; for newly introduced blocks, run the rule's
        reference-validity hook.

        Block types with no registered rule pass through unchecked —
        plain paragraphs, headers, etc. don't need a rule.
        """
        old_block_ids = cls._collect_block_ids(old_content)
        for block in new_content.blocks:
            rule = cls.get_rule(block.type)
            if rule is None:
                continue
            if host not in rule.allowed_contexts():
                raise BadRequestException(
                    f"{block.type} blocks are not allowed in {host.value} content."
                )
            if block.id not in old_block_ids:
                rule.validate_new_block(block)

    @staticmethod
    def _collect_block_ids(content: RichTextDTO | None) -> set[str]:
        if content is None:
            return set()
        return {block.id for block in content.blocks}
