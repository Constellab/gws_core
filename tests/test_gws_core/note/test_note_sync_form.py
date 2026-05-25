"""Note → space sync of embedded FORM blocks.

A note containing a FORM block must push a read-only snapshot of the form
(metadata + renderable values/specs) to space as ``<block_id>.json`` in the
multipart payload, mirroring how resource/file views are synced. A stale
block referencing a deleted form must be skipped without failing the sync.
"""

from unittest.mock import patch

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.service.external_api_service import FormData
from gws_core.folder.space_folder import SpaceFolder
from gws_core.form.form_dto import CreateFormDTO, FormSpaceSnapshotDTO
from gws_core.form.form_service import FormService
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockTypeStandard
from gws_core.note.note_dto import InsertFormReferenceBlockDTO, NoteSaveDTO
from gws_core.note.note_service import NoteService
from gws_core.space.space_service import SpaceService
from gws_core.test.base_test_case import BaseTestCase


class TestNoteSyncForm(BaseTestCase):
    def test_form_block_synced_as_snapshot(self):
        """A note with a FORM block sends a FormSpaceSnapshotDTO file."""
        form = self._make_form()
        folder = SpaceFolder(title="Folder").save()
        note = NoteService.create(NoteSaveDTO(title="N"))
        NoteService.insert_form_block_reference(
            note.id, InsertFormReferenceBlockDTO(form_id=form.id)
        )
        # Re-fetch: insert_form_block_reference persisted the block, so the
        # local handle is stale. Set the folder on the fresh row.
        note = NoteService.get_by_id_and_check(note.id)
        note.folder = folder
        note.save()

        with patch.object(SpaceService, "save_lab_note") as mock_save:
            NoteService._synchronize_with_space(NoteService.get_by_id_and_check(note.id))

        form_data: FormData = mock_save.call_args[0][2]
        # The snapshot is added under the "files" key, named "<block_id>.json".
        filenames = {fname for key, _, fname in form_data.file_paths if key == "files"}
        self.assertIn(form.id + ".json", filenames)

    def test_snapshot_dto_round_trip(self):
        """FormSpaceSnapshotDTO serializes and re-parses without loss."""
        form = self._make_form()
        snapshot = FormService.get_space_snapshot(form.id)
        reparsed = FormSpaceSnapshotDTO.from_json(snapshot.to_json_dict())
        self.assertEqual(reparsed.form.id, form.id)
        self.assertEqual(reparsed.form.name, form.name)
        self.assertIsNotNone(reparsed.content.specs)

    def test_form_snapshot_failure_is_skipped(self):
        """A form whose snapshot build fails is skipped, not fatal.

        A note can never legitimately hold a block pointing at a deleted
        form (NoteFormModel's RESTRICT FK forbids deleting a referenced
        form), so the skip branch is defensive. Simulate a DB-inconsistency
        failure by forcing get_space_snapshot to raise."""
        form = self._make_form()
        folder = SpaceFolder(title="Folder").save()
        note = NoteService.create(NoteSaveDTO(title="N"))
        NoteService.insert_form_block_reference(
            note.id, InsertFormReferenceBlockDTO(form_id=form.id)
        )
        note = NoteService.get_by_id_and_check(note.id)
        note.folder = folder
        note.save()

        with (
            patch.object(SpaceService, "save_lab_note") as mock_save,
            patch.object(FormService, "get_space_snapshot", side_effect=RuntimeError("boom")),
        ):
            # Must not raise — the failing block is skipped with a warning.
            NoteService._synchronize_with_space(NoteService.get_by_id_and_check(note.id))

        form_data: FormData = mock_save.call_args[0][2]
        self.assertEqual(form_data.file_paths, [])

    # ---------------- Helpers --------------------------------------------

    def _get_form_block_id(self, note_id: str) -> str:
        note = NoteService.get_by_id_and_check(note_id)
        rich_text = note.get_content_as_rich_text()
        blocks = rich_text.get_blocks_by_type(RichTextBlockTypeStandard.FORM)
        return blocks[0].id

    def _make_form(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="Demo"))
        draft = (
            FormTemplateVersion.select()
            .where(
                (FormTemplateVersion.template == template)
                & (FormTemplateVersion.status == FormTemplateVersionStatus.DRAFT)
            )
            .get()
        )
        draft.update_specs(ConfigSpecs({"name": StrParam(human_name="name", optional=True)}))
        version = FormTemplateService.publish_version(template.id, draft.id)
        return FormService.create(CreateFormDTO(template_version_id=version.id))
