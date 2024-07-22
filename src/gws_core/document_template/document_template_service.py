

from peewee import ModelSelect

from gws_core.document_template.document_template import DocumentTemplate
from gws_core.document_template.document_template_search_builder import \
    ReportTemplateSearchBuilder
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.report.report import Report
from gws_core.user.activity.activity_dto import (ActivityObjectType,
                                                 ActivityType)
from gws_core.user.activity.activity_service import ActivityService

from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import SearchBuilder, SearchParams
from ..core.decorator.transaction import transaction


class DocumentTemplateService():

    @classmethod
    @transaction()
    def create_empty(cls, title: str) -> DocumentTemplate:
        return cls._create(title)

    @classmethod
    @transaction()
    def create_from_report(cls, doc_id: str) -> DocumentTemplate:
        report: Report = Report.get_by_id_and_check(doc_id)

        return cls._create(report.title, report.content)

    @classmethod
    @transaction()
    def _create(cls, title: str, content: RichTextDTO = None) -> DocumentTemplate:
        document = DocumentTemplate()
        document.title = title

        rich_text = RichText(content)
        rich_text.replace_resource_views_with_parameters()

        # Set default content for document
        document.content = rich_text.get_content()

        document.save()

        ActivityService.add(ActivityType.CREATE,
                            object_type=ActivityObjectType.DOCUMENT_TEMPLATE,
                            object_id=document.id)

        return document

    @classmethod
    def update_title(cls, doc_id: str, title: str) -> DocumentTemplate:
        document: DocumentTemplate = cls.get_by_id_and_check(doc_id)

        document.title = title.strip()

        return document.save()

    @classmethod
    @transaction()
    def update_content(cls, doc_id: str, report_content: RichTextDTO) -> DocumentTemplate:
        document: DocumentTemplate = cls.get_by_id_and_check(doc_id)

        document.content = report_content

        return document.save()

    @classmethod
    @transaction()
    def delete(cls, doc_id: str) -> None:

        DocumentTemplate.delete_by_id(doc_id)

        ActivityService.add(ActivityType.DELETE,
                            object_type=ActivityObjectType.DOCUMENT_TEMPLATE,
                            object_id=doc_id)

    ################################################# GET ########################################

    @classmethod
    def get_by_id_and_check(cls, id: str) -> DocumentTemplate:
        return DocumentTemplate.get_by_id_and_check(id)

    @classmethod
    def search(cls,
               search: SearchParams,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[DocumentTemplate]:

        search_builder: SearchBuilder = ReportTemplateSearchBuilder()

        model_select: ModelSelect = search_builder.add_search_params(search).build_search()
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def search_by_name(cls, name: str,
                       page: int = 0,
                       number_of_items_per_page: int = 20) -> Paginator[DocumentTemplate]:
        model_select = DocumentTemplate.select().where(DocumentTemplate.title.contains(name))

        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)
