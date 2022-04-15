# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List

from fastapi import UploadFile
from gws_core.core.classes.rich_text_content import (RichText,
                                                     RichTextResourceView)
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.report.report_file_service import ReportFileService, ReportImage
from gws_core.resource.resource_service import ResourceService
from peewee import ModelSelect

from ..central.central_service import CentralService
from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import SearchBuilder, SearchDict
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
            if experiment.project.id != report.project.id:
                raise BadRequestException(GWSException.REPORT_VALIDATION_EXP_OTHER_PROJECT.value,
                                          GWSException.REPORT_VALIDATION_EXP_OTHER_PROJECT.name, {'title': experiment.title})

        return report.save()

    @classmethod
    def update_content(cls, report_id: str, report_content: Dict) -> Report:
        report: Report = cls._get_and_check_before_update(report_id)

        report.content = report_content
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
            if not experiment.is_validated:
                raise BadRequestException(GWSException.REPORT_VALIDATION_EXP_NOT_VALIDATED.value,
                                          GWSException.REPORT_VALIDATION_EXP_NOT_VALIDATED.name, {'title': experiment.title})

            if experiment.project.id != report.project.id:
                raise BadRequestException(GWSException.REPORT_VALIDATION_EXP_OTHER_PROJECT.value,
                                          GWSException.REPORT_VALIDATION_EXP_OTHER_PROJECT.name, {'title': experiment.title})

        # check that all resource views are from resource that
        # were generated by experiments that are linked to the report
        resource_views: List[RichTextResourceView] = rich_text.get_resource_views()
        for resource_view in resource_views:
            resource = ResourceService.get_resource_by_id(resource_view["resource_id"])

            # If the resource was generated by an experiment, check that the experiment is linked to the report
            if resource.experiment:
                if len([exp for exp in experiments if exp.id == resource.experiment.id]) == 0:
                    # get the best name for the error
                    view_name = resource_view["title"] or resource.name
                    raise BadRequestException(GWSException.REPORT_VALIDATION_RESOURCE_VIEW_OTHER_EXP.value,
                                              GWSException.REPORT_VALIDATION_RESOURCE_VIEW_OTHER_EXP.name,
                                              {'view_name': view_name, 'exp_title': resource.experiment.title})

        report.is_validated = True

        return report.save()

    @classmethod
    @transaction()
    def validate_and_send_to_central(cls, report_id: str, project_dto: ProjectDto = None) -> Report:
        report = cls.validate(report_id, project_dto)

        if Settings.is_local_env():
            Logger.info('Skipping sending experiment to central as we are running in LOCAL')
            return report

        json_: Dict = report.to_json(deep=True)

        # retrieve the experiment ids
        experiments: List[Experiment] = cls.get_experiments_by_report(report_id)
        json_["experimentIds"] = list(map(lambda x: x.id, experiments))

        rich_text = RichText(report.content)

        # retrieve all the figures file path
        figures = rich_text.get_figures()
        file_paths: List[str] = []

        for figure in figures:
            file_paths.append(ReportFileService.get_file_path(figure['filename']))

        # Save the experiment in central
        CentralService.save_report(report.project.id, json_, file_paths=file_paths)

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
               search: SearchDict,
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
    def delete_image(cls, filename: str) -> None:
        ReportFileService.delete_file(filename)

    ################################################# Resource View ########################################
