
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.form_template.form_template_dto import FormTemplateVersionStatus
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.impl.rich_text.block.rich_text_block_form_template import (
    RichTextBlockFormTemplate,
)
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_file_service import RichTextFileService
from gws_core.impl.rich_text.rich_text_form_validator import (
    RichTextFormBlockValidator,
)
from gws_core.impl.rich_text.rich_text_types import (
    RichTextBlock,
    RichTextDTO,
    RichTextObjectType,
)
from gws_core.note.note import Note
from gws_core.note_template.note_template import NoteTemplate
from gws_core.note_template.note_template_dto import InsertFormTemplateBlockDTO
from gws_core.note_template.note_template_search_builder import NoteTemplateSearchBuilder
from gws_core.user.activity.activity_dto import ActivityObjectType, ActivityType
from gws_core.user.activity.activity_service import ActivityService

from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import SearchBuilder, SearchParams


class NoteTemplateService:
    @classmethod
    @GwsCoreDbManager.transaction()
    def create_empty(cls, title: str) -> NoteTemplate:
        return cls._create(title)

    @classmethod
    @GwsCoreDbManager.transaction()
    def create_from_note(cls, note_id: str) -> NoteTemplate:
        note: Note = Note.get_by_id_and_check(note_id)

        note_template = cls._create(note.title, note.content)

        # copy the storage of the note to the note template
        RichTextFileService.copy_object_dir(
            RichTextObjectType.NOTE, note_id, RichTextObjectType.NOTE_TEMPLATE, note_template.id
        )

        return note_template

    @classmethod
    @GwsCoreDbManager.transaction()
    def _create(cls, title: str, content: RichTextDTO | None = None) -> NoteTemplate:
        document = NoteTemplate()
        document.title = title

        rich_text = RichText(content)
        rich_text.replace_resource_views_with_parameters()

        # Set default content for document
        document.content = rich_text.to_dto()

        document.save()

        ActivityService.add(
            ActivityType.CREATE, object_type=ActivityObjectType.NOTE_TEMPLATE, object_id=document.id
        )

        return document

    @classmethod
    def update_title(cls, doc_id: str, title: str) -> NoteTemplate:
        document: NoteTemplate = cls.get_by_id_and_check(doc_id)

        document.title = title.strip()

        return document.save()

    @classmethod
    @GwsCoreDbManager.transaction()
    def update_content(cls, doc_id: str, note_content: RichTextDTO) -> NoteTemplate:
        document: NoteTemplate = cls.get_by_id_and_check(doc_id)

        # Reject FORM blocks; reject newly-introduced FORM_TEMPLATE blocks
        # whose pinned version is not PUBLISHED (spec §5.1).
        RichTextFormBlockValidator.validate_for_note_template(
            note_content, document.content
        )

        document.content = note_content

        return document.save()

    @classmethod
    @GwsCoreDbManager.transaction()
    def insert_form_template_block(
        cls, doc_id: str, dto: InsertFormTemplateBlockDTO,
    ) -> NoteTemplate:
        """Insert a FORM_TEMPLATE block referencing a PUBLISHED
        FormTemplateVersion. ``form_template_id`` is derived from the
        version. See spec §5.5.
        """
        document: NoteTemplate = cls.get_by_id_and_check(doc_id)

        version = FormTemplateVersion.get_by_id_and_check(dto.form_template_version_id)
        if version.status != FormTemplateVersionStatus.PUBLISHED:
            raise BadRequestException(
                "Can only insert a FORM_TEMPLATE block referencing a "
                f"PUBLISHED version, but this version has status "
                f"{version.status.value}."
            )

        ft_block_data = RichTextBlockFormTemplate(
            form_template_id=version.template_id,
            form_template_version_id=version.id,
            display_name=dto.display_name,
        )
        block = RichTextBlock.from_data(ft_block_data)

        rich_text = document.get_content_as_rich_text()
        if dto.position is None:
            rich_text.append_block(block)
        else:
            rich_text.insert_block_at_index(dto.position, block)

        return cls.update_content(doc_id, rich_text.to_dto())

    @classmethod
    def delete(cls, doc_id: str) -> None:
        # delete the object in the database
        cls._delete_in_db(doc_id)

        # if transaction is successful, delete the object in the file system
        RichTextFileService.delete_object_dir(RichTextObjectType.NOTE_TEMPLATE, doc_id)

    @classmethod
    @GwsCoreDbManager.transaction()
    def _delete_in_db(cls, doc_id: str) -> None:
        NoteTemplate.delete_by_id(doc_id)

        ActivityService.add(
            ActivityType.DELETE, object_type=ActivityObjectType.NOTE_TEMPLATE, object_id=doc_id
        )

    ################################################# GET ########################################

    @classmethod
    def get_by_id_and_check(cls, id: str) -> NoteTemplate:
        return NoteTemplate.get_by_id_and_check(id)

    @classmethod
    def search(
        cls, search: SearchParams, page: int = 0, number_of_items_per_page: int = 20
    ) -> Paginator[NoteTemplate]:
        search_builder: SearchBuilder = NoteTemplateSearchBuilder()

        return search_builder.add_search_params(search).search_page(page, number_of_items_per_page)

    @classmethod
    def search_by_name(
        cls, name: str, page: int = 0, number_of_items_per_page: int = 20
    ) -> Paginator[NoteTemplate]:
        model_select = NoteTemplate.select().where(NoteTemplate.title.contains(name))

        return Paginator(model_select, page=page, nb_of_items_per_page=number_of_items_per_page)
