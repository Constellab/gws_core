# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi import UploadFile
from fastapi.responses import FileResponse
from peewee import ModelSelect

from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.report.report import Report
from gws_core.report.report_dto import ReportImageDTO
from gws_core.report.report_file_service import ReportFileService
from gws_core.report.template.report_template import ReportTemplate
from gws_core.report.template.report_template_search_builder import \
    ReportTemplateSearchBuilder
from gws_core.user.activity.activity_dto import (ActivityObjectType,
                                                 ActivityType)
from gws_core.user.activity.activity_service import ActivityService

from ...core.classes.paginator import Paginator
from ...core.classes.search_builder import SearchBuilder, SearchParams
from ...core.decorator.transaction import transaction


class ReportTemplateService():

    @classmethod
    @transaction()
    def create_empty(cls, title: str) -> ReportTemplate:
        return cls._create(title)

    @classmethod
    @transaction()
    def create_from_report(cls, report_id: str) -> ReportTemplate:
        report: Report = Report.get_by_id_and_check(report_id)

        return cls._create(report.title, report.content)

    @classmethod
    @transaction()
    def _create(cls, title: str, content: RichTextDTO = None) -> ReportTemplate:
        report = ReportTemplate()
        report.title = title

        rich_text = RichText(content)
        rich_text.replace_resource_views_with_variables()

        # Set default content for report
        report.content = rich_text.get_content()

        report.save()

        ActivityService.add(ActivityType.CREATE,
                            object_type=ActivityObjectType.REPORT_TEMPLATE,
                            object_id=report.id)

        return report

    @classmethod
    def update_title(cls, report_id: str, title: str) -> ReportTemplate:
        report: ReportTemplate = cls.get_by_id_and_check(report_id)

        report.title = title.strip()

        return report.save()

    @classmethod
    @transaction()
    def update_content(cls, report_id: str, report_content: RichTextDTO) -> ReportTemplate:
        report: ReportTemplate = cls.get_by_id_and_check(report_id)

        report.content = report_content

        return report.save()

    @classmethod
    @transaction()
    def delete(cls, report_id: str) -> None:

        ReportTemplate.delete_by_id(report_id)

        ActivityService.add(ActivityType.DELETE,
                            object_type=ActivityObjectType.REPORT_TEMPLATE,
                            object_id=report_id)

    ################################################# GET ########################################

    @classmethod
    def get_by_id_and_check(cls, id: str) -> ReportTemplate:
        return ReportTemplate.get_by_id_and_check(id)

    @classmethod
    def search(cls,
               search: SearchParams,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[ReportTemplate]:

        search_builder: SearchBuilder = ReportTemplateSearchBuilder()

        model_select: ModelSelect = search_builder.add_search_params(search).build_search()
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def search_by_name(cls, name: str,
                       page: int = 0,
                       number_of_items_per_page: int = 20) -> Paginator[ReportTemplate]:
        model_select = ReportTemplate.select().where(ReportTemplate.title.contains(name))

        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    ################################################# Image ########################################

    @classmethod
    def upload_image(cls, file: UploadFile) -> ReportImageDTO:
        return ReportFileService.upload_file(file)

    @classmethod
    def get_image_path(cls, filename: str) -> str:
        return ReportFileService.get_file_path(filename)

    @classmethod
    def get_image_file_response(cls, filename: str) -> FileResponse:
        file_path = cls.get_image_path(filename)
        return FileHelper.create_file_response(file_path, filename=filename)

    @classmethod
    def delete_image(cls, filename: str) -> None:
        ReportFileService.delete_file(filename)
