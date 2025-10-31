

from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_file_service import RichTextFileService
from gws_core.impl.rich_text.rich_text_types import (RichTextDTO,
                                                     RichTextObjectType)
from gws_core.note.note import Note
from gws_core.note_template.note_template import NoteTemplate
from gws_core.note_template.note_template_search_builder import \
    NoteTemplateSearchBuilder
from gws_core.user.activity.activity_dto import (ActivityObjectType,
                                                 ActivityType)
from gws_core.user.activity.activity_service import ActivityService
from peewee import ModelSelect

from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import SearchBuilder, SearchParams


class NoteTemplateService():

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
        RichTextFileService.copy_object_dir(RichTextObjectType.NOTE, note_id,
                                            RichTextObjectType.NOTE_TEMPLATE,
                                            note_template.id)

        return note_template

    @classmethod
    @GwsCoreDbManager.transaction()
    def _create(cls, title: str, content: RichTextDTO = None) -> NoteTemplate:
        document = NoteTemplate()
        document.title = title

        rich_text = RichText(content)
        rich_text.replace_resource_views_with_parameters()

        # Set default content for document
        document.content = rich_text.to_dto()

        document.save()

        ActivityService.add(ActivityType.CREATE,
                            object_type=ActivityObjectType.NOTE_TEMPLATE,
                            object_id=document.id)

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

        document.content = note_content

        return document.save()

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

        ActivityService.add(ActivityType.DELETE,
                            object_type=ActivityObjectType.NOTE_TEMPLATE,
                            object_id=doc_id)

    ################################################# GET ########################################

    @classmethod
    def get_by_id_and_check(cls, id: str) -> NoteTemplate:
        return NoteTemplate.get_by_id_and_check(id)

    @classmethod
    def search(cls,
               search: SearchParams,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[NoteTemplate]:

        search_builder: SearchBuilder = NoteTemplateSearchBuilder()

        return search_builder.add_search_params(search).search_page(page, number_of_items_per_page)

    @classmethod
    def search_by_name(cls, name: str,
                       page: int = 0,
                       number_of_items_per_page: int = 20) -> Paginator[NoteTemplate]:
        model_select = NoteTemplate.select().where(NoteTemplate.title.contains(name))

        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)
