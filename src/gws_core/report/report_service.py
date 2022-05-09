# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List, Set

from fastapi import UploadFile
from fastapi.responses import FileResponse
from gws_core.central.central_dto import SaveReportToCentralDTO
from gws_core.core.classes.rich_text_content import (RichText, RichTextI,
                                                     RichTextResourceView)
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.impl.file.file_helper import FileHelper
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.report.report_file_service import ReportFileService, ReportImage
from gws_core.report.report_resource import ReportResource
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view_config.view_config_service import ViewConfigService
from gws_core.resource.view_types import report_supported_views
from gws_core.task.task_input_model import TaskInputModel
from peewee import ModelSelect

from ..central.central_service import CentralService
from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import SearchBuilder, SearchParams
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..experiment.experiment import Experiment
from ..project.project_dto import ProjectDto
from ..project.project_service import ProjectService
from ..report.report_dto import ReportDTO
from ..report.report_search_builder import ReportSearchBuilder
from .report import Report, ReportExperiment


class ReportService():

    @classmethod
    @transaction()
    def create(cls, report_dto: ReportDTO, experiment_ids: List[str] = None) -> Report:
        report = Report()
        report.title = report_dto.title
        report.project = ProjectService.get_or_create_project_from_dto(report_dto.project)

        # Set default content for report
        report.content = {
            "ops":
            [{"insert": "Introduction"},
             {"attributes": {"header": 1},
              "insert": "\n"},
             {"insert": "\n\nMethods"},
             {"attributes": {"header": 1},
              "insert": "\n"},
             {"insert": "\n\nResults"},
             {"attributes": {"header": 1},
              "insert": "\n"},
             {"insert": "\n\nConclusion"},
             {"attributes": {"header": 1},
              "insert": "\n"},
             {"insert": "\n\nReferences"},
             {"attributes": {"header": 1},
              "insert": "\n"},
             {"insert": "\n"}]}

        report.save()

        if experiment_ids is not None:
            # Create the ReportExperiment
            for experiment_id in experiment_ids:
                cls.add_experiment(report.id, experiment_id)

        return report

    @classmethod
    def update(cls, report_id: str, report_dto: ReportDTO) -> Report:
        report: Report = cls._get_and_check_before_update(report_id)

        report.title = report_dto.title
        report.project = ProjectService.get_or_create_project_from_dto(report_dto.project)

        # check that all associated experiment are in same project
        experiments: List[Experiment] = cls.get_experiments_by_report(report_id)

        for experiment in experiments:
            if experiment.project is None:
                raise BadRequestException(GWSException.REPORT_VALIDATION_EXP_NO_PROJECT.value,
                                          GWSException.REPORT_VALIDATION_EXP_NO_PROJECT.name, {'title': experiment.title})

            if experiment.project.id != report.project.id:
                raise BadRequestException(GWSException.REPORT_VALIDATION_EXP_OTHER_PROJECT.value,
                                          GWSException.REPORT_VALIDATION_EXP_OTHER_PROJECT.name, {'title': experiment.title},
                                          )

        return report.save()

    @classmethod
    @transaction()
    def update_content(cls, report_id: str, report_content: RichTextI) -> Report:
        report: Report = cls._get_and_check_before_update(report_id)

        report.content = report_content
        # refresh ReportResource table
        cls._refresh_report_associated_resources(report)

        return report.save()

    @classmethod
    def delete(cls, report_id: str) -> None:
        cls._get_and_check_before_update(report_id)

        Report.delete_by_id(report_id)

    @classmethod
    def validate(cls, report_id: str, project_dto: ProjectDto = None) -> Report:
        report: Report = cls._get_and_check_before_update(report_id)

        rich_text = RichText(report.content)
        if rich_text.is_empty():
            raise BadRequestException('The report is empty')

        # set the project if it is provided
        if project_dto is not None:
            report.project = ProjectService.get_or_create_project_from_dto(project_dto)

        if report.project is None:
            raise BadRequestException("The report must be associated to a project to be validated")

        # check that all associated experiment are validated and are in same project
        experiments: List[Experiment] = cls.get_experiments_by_report(report_id)
        for experiment in experiments:
            if experiment.project and experiment.project.id != report.project.id:
                raise BadRequestException(GWSException.REPORT_VALIDATION_EXP_OTHER_PROJECT.value,
                                          GWSException.REPORT_VALIDATION_EXP_OTHER_PROJECT.name, {'title': experiment.title})

        # validate experiment that were not validated
        for experiment in experiments:
            if not experiment.is_validated:
                ExperimentService.validate_experiment(experiment, report.project)

        # refresh the associated resource (for precaution)
        cls._refresh_report_associated_resources(report)
        # check that all resource views are from resource that
        # were generated by experiments that are linked to the report
        resource_views: List[RichTextResourceView] = rich_text.get_resource_views()
        experiment_ids = [experiment.id for experiment in experiments]
        for resource_view in resource_views:
            resource = ResourceService.get_resource_by_id(resource_view["resource_id"])

            view_name = resource_view.get("title") or resource.name
            # If the resource was generated by an experiment, check that the experiment is linked to the report
            if resource.origin == ResourceOrigin.GENERATED:
                if not resource.experiment.id in experiment_ids:
                    # get the best name for the error
                    raise BadRequestException(GWSException.REPORT_VALIDATION_RESOURCE_GENERATED_VIEW_OTHER_EXP.value,
                                              GWSException.REPORT_VALIDATION_RESOURCE_GENERATED_VIEW_OTHER_EXP.name,
                                              {'view_name': view_name, 'exp_title': resource.experiment.title})
            else:
                if not TaskInputModel.resource_is_used_by_experiment(resource.id, experiment_ids):
                    raise BadRequestException(GWSException.REPORT_VALIDATION_RESOURCE_UPLOADED_VIEW_OTHER_EXP.value,
                                              GWSException.REPORT_VALIDATION_RESOURCE_UPLOADED_VIEW_OTHER_EXP.name,
                                              {'view_name': view_name, 'resource_name': resource.name})

        report.validate()

        return report.save()

    @classmethod
    @transaction()
    def validate_and_send_to_central(cls, report_id: str, project_dto: ProjectDto = None) -> Report:
        report = cls.validate(report_id, project_dto)

        if Settings.is_local_env():
            Logger.info('Skipping sending experiment to central as we are running in LOCAL')
            return report

        # retrieve the experiment ids
        experiments: List[Experiment] = cls.get_experiments_by_report(report_id)

        lab_config: LabConfigModel = report.lab_config or LabConfigModel.get_current_config()

        save_report_dto: SaveReportToCentralDTO = {
            "report": report.to_json(deep=True),
            "experiment_ids": [experiment.id for experiment in experiments],
            "lab_config": lab_config.to_json(),
        }
        # Save the experiment in central
        CentralService.save_report(report.project.id, save_report_dto)

        return report

    @classmethod
    @transaction()
    def add_experiment(cls, report_id: str, experiment_id: str) -> Experiment:
        report: Report = cls._get_and_check_before_update(report_id)

        experiments: List[Experiment] = cls.get_experiments_by_report(report_id)

        for experiment in experiments:
            # If the experiment was already added to the report
            if experiment.id == experiment_id:
                raise BadRequestException(GWSException.REPORT_EXP_ALREADY_ASSOCIATED.value,
                                          GWSException.REPORT_EXP_ALREADY_ASSOCIATED.name)

        experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

        # check projects
        if report.project is None:
            # if the report is not associated with a project, associate it with the project of the experiment
            if experiment.project is not None:
                report.project = experiment.project
                report.save()
        else:
            # check if the report project is the same as the experiment project
            if experiment.project is not None and report.project.id != experiment.project.id:
                raise BadRequestException(GWSException.REPORT_ADD_EXP_OTHER_PROJECT.value,
                                          GWSException.REPORT_ADD_EXP_OTHER_PROJECT.name)

        ReportExperiment.create_obj(experiment, report).save()
        return experiment

    @classmethod
    def remove_experiment(cls, report_id: str, experiment_id: str) -> None:
        cls._get_and_check_before_update(report_id)

        ReportExperiment.delete_obj(experiment_id, report_id)

    @classmethod
    def _get_and_check_before_update(cls, report_id: str) -> Report:
        """Retrieve the report and check if it's updatable or deletable

        :param report_id: [description]
        :type report_id: str
        :raises BadRequestException: [description]
        :return: [description]
        :rtype: Report
        """
        report: Report = Report.get_by_id_and_check(report_id)

        if report.is_validated:
            raise BadRequestException(GWSException.REPORT_VALIDATED.value, GWSException.REPORT_VALIDATED.name)

        return report

    ################################################# GET ########################################

    @classmethod
    def get_by_id_and_check(cls, id: str) -> Report:
        return Report.get_by_id_and_check(id)

    @classmethod
    def get_by_experiment(cls, experiment_id: str) -> List[Report]:
        return list(Report.select().join(ReportExperiment).where(
            ReportExperiment.experiment == experiment_id).order_by(
            Report.last_modified_at.desc()))

    @classmethod
    def get_experiments_by_report(cls, report_id: str) -> List[Experiment]:
        return list(Experiment.select().join(ReportExperiment).where(
            ReportExperiment.report == report_id).order_by(
            Experiment.last_modified_at.desc()))

    @classmethod
    def search(cls,
               search: SearchParams,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[Report]:

        search_builder: SearchBuilder = ReportSearchBuilder()

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, number_of_items_per_page=number_of_items_per_page)

    ################################################# Image ########################################

    @classmethod
    def upload_image(cls, file: UploadFile) -> ReportImage:
        return ReportFileService.upload_file(file)

    @classmethod
    def get_image_path(cls, filename: str) -> str:
        return ReportFileService.get_file_path(filename)

    @classmethod
    def get_image_file_response(cls, filename: str) -> FileResponse:
        file_path = cls.get_image_path(filename)
        return FileResponse(file_path, media_type=FileHelper.get_mime(file_path),
                            filename=filename)

    @classmethod
    def delete_image(cls, filename: str) -> None:
        ReportFileService.delete_file(filename)

    ################################################# Resource View ########################################
    @classmethod
    def search_available_resource_view(cls, report_id: str, search: SearchParams,
                                       page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ResourceModel]:
        """Method to search the resource views that are available for a report. It searches in the resource view in view config
        """

        # add a filter on experiments of the report
        experiments = ReportService.get_experiments_by_report(report_id)

        if len(experiments) == 0:
            raise BadRequestException(GWSException.REPORT_NO_ASSOCIATED_EXPERIMENT.value,
                                      GWSException.REPORT_NO_ASSOCIATED_EXPERIMENT.name)

        experiment_ids = [experiment.id for experiment in experiments]

        # retrieve the resources associated with the experiments
        resources = ResourceService.get_experiments_resources(experiment_ids)
        resource_ids = [resource.id for resource in resources]

        return ViewConfigService.search_by_resources(
            resource_ids, report_supported_views, search, page, number_of_items_per_page)

    @classmethod
    def _refresh_report_associated_resources(cls, report: Report) -> None:
        """Method to refresh the associated resources of a report. It will remove unassociated resources and
        add the new ones.
        """

        report_resources: List[ReportResource] = ReportResource.get_by_report(report.id)

        # extract resources ids form report_resources
        content_resources: Set[str] = RichText(report.content).get_associated_resources()

        # detect which resources views were removed and unassociate resource
        for report_resource in report_resources:
            if report_resource.resource.id not in content_resources:
                report_resource.delete_instance()

        # detect which resources views were added and associate resource
        db_resources = {report_resource.resource.id for report_resource in report_resources}
        for content_resource in content_resources:
            if content_resource not in db_resources:
                # create the link in DB
                ReportResource(report=report,
                               resource=ResourceModel(id=content_resource)).save()
