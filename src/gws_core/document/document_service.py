
from enum import Enum
from typing import Optional, Type

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.decorator.transaction import transaction
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.document.document import Document
from gws_core.document.document_dto import DocumentSaveDTO
from gws_core.document.document_search_builder import DocumentSearchBuilder
from gws_core.document_template.document_template import DocumentTemplate
from gws_core.impl.rich_text.rich_text_file_service import RichTextFileService
from gws_core.impl.rich_text.rich_text_types import RichTextObjectType
from gws_core.project.project import Project
from gws_core.report.report import Report
from gws_core.user.activity.activity_dto import (ActivityObjectType,
                                                 ActivityType)
from gws_core.user.activity.activity_service import ActivityService


class DocumentType(Enum):
    REPORT = "REPORT"
    NOTE = "NOTE"


class DocumentService():

    document_type: DocumentType
    document_model_type: Type[Document]
    rich_text_object_type: RichTextObjectType
    activity_object_type: ActivityObjectType

    def __init__(self, document_type: DocumentType,
                 document_model_type: Type[Document],
                 rich_text_object_type: RichTextObjectType,
                 activity_object_type: ActivityObjectType):
        self.document_type = document_type
        self.document_model_type = document_model_type
        self.rich_text_object_type = rich_text_object_type
        self.activity_object_type = activity_object_type

    def create(self, document_dto: DocumentSaveDTO) -> Document:
        document = self.document_model_type()
        document.title = document_dto.title
        document.project = Project.get_by_id_and_check(document_dto.project_id) if document_dto.project_id else None

        if document_dto.template_id:
            template: DocumentTemplate = DocumentTemplate.get_by_id_and_check(document_dto.template_id)
            document.content = template.content

            # copy the storage of the document template to the correct destination
            RichTextFileService.copy_object_dir(RichTextObjectType.DOCUMENT_TEMPLATE,
                                                template.id,
                                                self.rich_text_object_type,
                                                document.id)

        else:
            # Set default content for report
            document.content = self.document_model_type.get_default_content()

        document.save()

        ActivityService.add(ActivityType.CREATE,
                            object_type=self.activity_object_type,
                            object_id=document.id)

        return document

    def update_title(self, document_id: str, title: str) -> Document:
        document: Document = self.get_and_check_before_update(document_id)

        document.title = title.strip()

        document = document.save()

        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=self.activity_object_type,
                                            object_id=document.id)

        return document

    def update_project(self, document_id: str, project_id: Optional[str]) -> Document:
        document: Document = self.get_and_check_before_update(document_id)

        # update project
        if project_id:
            project = Project.get_by_id_and_check(project_id)
            if document.last_sync_at is not None and project != document.project:
                raise BadRequestException(
                    f"You can't change the project of {document.get_entity_type_human_name()} that has been synced. You must unlink it from the project first.")
            document.project = project
        else:
            document.project = None

        document = document.save()

        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=self.activity_object_type,
                                            object_id=document.id)

        return document

    def get_and_check_before_update(self, doc_id: str) -> Document:
        """Retrieve the report and check if it's updatable or deletable

        :param report_id: [description]
        :type report_id: str
        :raises BadRequestException: [description]
        :return: [description]
        :rtype: Report
        """
        document = Document.get_by_id_and_check(doc_id)

        document.check_is_updatable()

        return document

    ################################################# Search ########################################
    def search(self,
               search: SearchParams,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[Document]:

        search_builder = DocumentSearchBuilder(self.document_model_type,
                                               self.document_model_type.get_entity_type())

        model_select = search_builder.add_search_params(search).build_search()
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    def search_by_name(self, name: str,
                       page: int = 0,
                       number_of_items_per_page: int = 20) -> Paginator[Document]:
        model_select = self.document_model_type.select().where(self.document_model_type.title.contains(name))

        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    ################################################# ARCHIVE ########################################

    @transaction()
    def archive(self, document_id: str) -> Document:
        document = self.document_model_type.get_by_id_and_check(document_id)

        if document.is_archived:
            raise BadRequestException(f'The {document.get_entity_type_human_name()} is already archived')

        ActivityService.add(
            ActivityType.ARCHIVE,
            object_type=self.activity_object_type,
            object_id=document_id
        )
        return document.archive(True)

    @transaction()
    def unarchive(self, document_id: str) -> Document:
        document: Document = Document.get_by_id_and_check(document_id)

        if not document.is_archived:
            raise BadRequestException(f'The {document.get_entity_type_human_name()} is not archived')

        ActivityService.add(
            ActivityType.UNARCHIVE,
            object_type=self.activity_object_type,
            object_id=document_id
        )
        return document.archive(False)
