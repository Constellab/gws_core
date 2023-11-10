# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Callable, List, Set

from fastapi import UploadFile
from fastapi.responses import FileResponse
from peewee import ModelSelect

from gws_core.core.classes.rich_text_content import (RichText, RichTextI,
                                                     RichTextResourceView)
from gws_core.core.utils.date_helper import DateHelper
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.impl.file.file_helper import FileHelper
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.project.project import Project
from gws_core.report.report_file_service import ReportFileService, ReportImage
from gws_core.report.report_resource_model import ReportResourceModel
from gws_core.report.template.report_template import ReportTemplate
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view.view_types import exluded_views_in_historic
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.resource.view_config.view_config_service import ViewConfigService
from gws_core.space.space_dto import SaveReportToSpaceDTO
from gws_core.task.task_input_model import TaskInputModel
from gws_core.user.activity.activity import ActivityObjectType, ActivityType
from gws_core.user.activity.activity_service import ActivityService
from gws_core.user.current_user_service import CurrentUserService

from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import SearchBuilder, SearchParams
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..experiment.experiment import Experiment
from ..report.report_dto import ReportDTO
from ..report.report_search_builder import ReportSearchBuilder
from ..space.space_service import SpaceService
from .report import Report, ReportExperiment


class ReportService():

    @classmethod
    @transaction()
    def create(cls, report_dto: ReportDTO, experiment_ids: List[str] = None) -> Report:
        report = Report()
        report.title = report_dto.title
        report.project = Project.get_by_id_and_check(report_dto.project_id) if report_dto.project_id else None

        if report_dto.template_id:
            template: ReportTemplate = ReportTemplate.get_by_id_and_check(report_dto.template_id)
            report.content = template.content
        else:
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

        ActivityService.add(ActivityType.CREATE,
                            object_type=ActivityObjectType.REPORT,
                            object_id=report.id)

        return report

    @classmethod
    def update(cls, report_id: str, report_dto: ReportDTO) -> Report:
        report: Report = cls._get_and_check_before_update(report_id)

        report.title = report_dto.title.strip()

        cls._update_report_project(report, report_dto.project_id)

        return report.save()

    @classmethod
    def update_title(cls, report_id: str, title: str) -> Report:
        report: Report = cls._get_and_check_before_update(report_id)

        report.title = title.strip()

        return report.save()

    @classmethod
    def update_project(cls, report_id: str, project_id: str) -> Report:
        report: Report = cls._get_and_check_before_update(report_id)

        cls._update_report_project(report, project_id)

        return report.save()

    @classmethod
    def _update_report_project(cls, report: Report, project_id: str) -> Report:
        # update project
        if project_id:
            project = Project.get_by_id_and_check(project_id)
            if report.last_sync_at is not None and project != report.project:
                raise BadRequestException("You can't change the project of an experiment that has been synced")
            report.project = project

        # if the project was removed
        if project_id is None and report.project is not None:
            report.project = None

            if report.last_sync_at is not None:
                # delete the report in space
                SpaceService.delete_report(project_id=report.project.id, report_id=report.id)

        # check that all associated experiment are in same project
        experiments: List[Experiment] = cls.get_experiments_by_report(report.id)

        for experiment in experiments:
            if experiment.project is None:
                raise BadRequestException(GWSException.REPORT_VALIDATION_EXP_NO_PROJECT.value,
                                          GWSException.REPORT_VALIDATION_EXP_NO_PROJECT.name, {'title': experiment.title})

            if experiment.project.id != report.project.id:
                raise BadRequestException(GWSException.REPORT_VALIDATION_EXP_OTHER_PROJECT.value,
                                          GWSException.REPORT_VALIDATION_EXP_OTHER_PROJECT.name, {'title': experiment.title})

    @classmethod
    @transaction()
    def update_content(cls, report_id: str, report_content: RichTextI) -> Report:
        report: Report = cls._get_and_check_before_update(report_id)

        report.content = report_content
        # refresh ReportResource table
        cls._refresh_report_associated_resources(report)

        return report.save()

    @classmethod
    @transaction()
    def add_view_to_content(cls, report_id: str, view_config_id: str) -> Report:
        report: Report = cls._get_and_check_before_update(report_id)

        view_config: ViewConfig = ViewConfigService.get_by_id(view_config_id)

        if view_config.view_type in exluded_views_in_historic:
            raise BadRequestException("You can't add this type of view to a report")

        # create the json object for the rich text
        view_content: RichTextResourceView = view_config.to_rich_text_resource_view()

        # get the rich text and add the resource view
        rich_text = report.get_content_as_rich_text()
        rich_text.add_resource_views(view_content)

        report = cls.update_content(report_id, rich_text.get_content())

        # if the view is associated to an experiment, link it to the report
        if view_config.experiment:
            cls.add_experiment(report_id, view_config.experiment.id, False)

        return report

    @classmethod
    @transaction()
    def delete(cls, report_id: str) -> None:
        report: Report = cls._get_and_check_before_update(report_id)

        Report.delete_by_id(report_id)

        # if the report was sync with space, delete it in space too
        if report.last_sync_at is not None and report.project is not None:
            SpaceService.delete_report(report.project.id, report.id)

        ActivityService.add(ActivityType.DELETE,
                            object_type=ActivityObjectType.REPORT,
                            object_id=report_id)

    @classmethod
    @transaction()
    def _validate(cls, report_id: str, project_id: str = None) -> Report:
        report: Report = cls._get_and_check_before_update(report_id)

        rich_text = RichText(report.content)
        if rich_text.is_empty():
            raise BadRequestException('The report is empty')

        # set the project if it is provided
        if project_id is not None:
            report.project = Project.get_by_id_and_check(project_id)

        if report.project is None:
            raise BadRequestException("The report must be associated to a project to be validated")

        if report.project.children.count() > 0:
            raise BadRequestException(
                "The experiment must be associated with a leaf project (project with no children)")

        # check that all associated experiment are validated and are in same project
        experiments: List[Experiment] = cls.get_experiments_by_report(report_id)
        for experiment in experiments:
            if experiment.project and experiment.project.id != report.project.id:
                raise BadRequestException(GWSException.REPORT_VALIDATION_EXP_OTHER_PROJECT.value,
                                          GWSException.REPORT_VALIDATION_EXP_OTHER_PROJECT.name, {'title': experiment.title})

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
            if not resource.is_manually_generated():
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

        # validate experiment that were not validated
        for experiment in experiments:
            if not experiment.is_validated:
                experiment.project = report.project
                ExperimentService.validate_experiment(experiment)

        report.validate()

        ActivityService.add(ActivityType.VALIDATE,
                            object_type=ActivityObjectType.REPORT,
                            object_id=report.id)

        return report.save()

    @classmethod
    @transaction()
    def validate_and_send_to_space(cls, report_id: str, project_id: str = None) -> Report:
        report = cls._validate(report_id, project_id)

        report = cls._synchronize_with_space(report)

        return report.save()

    ###################################  SYNCHRO WITH SPACE  ##############################
    @classmethod
    def synchronize_with_space_by_id(cls, id: str) -> Report:
        report: Report = cls.get_by_id_and_check(id)

        # retrieve the experiment ids
        experiments: List[Experiment] = cls.get_experiments_by_report(report.id)
        # syncronize the experiments that are not validated
        for experiment in experiments:
            if not experiment.is_validated:
                ExperimentService.synchronize_with_space_by_id(experiment.id)

        report = cls._synchronize_with_space(report)
        return report.save()

    @classmethod
    def _synchronize_with_space(cls, report: Report) -> Report:
        # if Settings.is_local_env():
        #     Logger.info('Skipping sending report to space as we are running in LOCAL')
        #     return report

        if report.project is None:
            raise BadRequestException("The experiment must be linked to a project before validating it")

        report.last_sync_at = DateHelper.now_utc()
        report.last_sync_by = CurrentUserService.get_and_check_current_user()

        # retrieve the experiment ids
        experiments: List[Experiment] = cls.get_experiments_by_report(report.id)

        lab_config: LabConfigModel = report.lab_config or LabConfigModel.get_current_config()

        save_report_dto: SaveReportToSpaceDTO = {
            "report": report.to_json(deep=True),
            "experiment_ids": [experiment.id for experiment in experiments],
            "lab_config": lab_config.to_json(),
            "resource_views": {}
        }

        rich_text = RichText(report.content)

        # retrieve all the figures file path
        file_paths: List[str] = []

        for figure in rich_text.get_figures():
            file_paths.append(ReportFileService.get_file_path(figure['filename']))

        # set the resource views in the json object
        for resource_view in rich_text.get_resource_views():
            # set the json view in the resource_views object
            # with the view id as key
            view_result = ResourceService.get_and_call_view_on_resource_model(
                resource_view["resource_id"],
                resource_view["view_method_name"],
                resource_view["view_config"])
            save_report_dto["resource_views"][resource_view["id"]] = view_result.to_json()
        # Save the experiment in space
        SpaceService.save_report(report.project.id, save_report_dto, file_paths)

        return report

    ###################################  ASSOCIATED EXPERIMENT  ##############################

    @classmethod
    @transaction()
    def add_experiment(cls, report_id: str, experiment_id: str,
                       error_if_already_associated: bool = True) -> Experiment:
        report: Report = cls._get_and_check_before_update(report_id)

        report_exp: ReportExperiment = ReportExperiment.find_by_pk(experiment_id, report_id).first()

        # If the experiment was already added to the report
        if report_exp is not None:

            if error_if_already_associated:
                raise BadRequestException(GWSException.REPORT_EXP_ALREADY_ASSOCIATED.value,
                                          GWSException.REPORT_EXP_ALREADY_ASSOCIATED.name)
            else:
                return report_exp.experiment

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

        report.check_is_updatable()

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

        model_select: ModelSelect = search_builder.add_search_params(search).build_search()
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def search_by_name(cls, name: str,
                       page: int = 0,
                       number_of_items_per_page: int = 20) -> Paginator[Report]:
        model_select = Report.select().where(Report.title.contains(name))

        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_by_resource(cls, resource_id: str,
                        page: int = 0,
                        number_of_items_per_page: int = 20) -> Paginator[Report]:
        query = ReportResourceModel.get_by_resource(resource_id).join(
            Report).order_by(ReportResourceModel.report.last_modified_at.desc())

        paginator: Paginator[ReportResourceModel] = Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)

        map_function: Callable[[ReportResourceModel], Experiment] = lambda x: x.report
        paginator.map_result(map_function)
        return paginator

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
        return FileHelper.create_file_response(file_path, filename=filename)

    @classmethod
    def delete_image(cls, filename: str) -> None:
        ReportFileService.delete_file(filename)

    ################################################# Resource View ########################################
    @classmethod
    def get_resources_of_associated_experiments(cls, report_id: str) -> List[ResourceModel]:
        """Method to retrieve the resources of the experiments associated with a report.
        Resources used as input or output of the experiments are returned.
        """
        # add a filter on experiments of the report
        experiments = ReportService.get_experiments_by_report(report_id)

        if len(experiments) == 0:
            raise BadRequestException(GWSException.REPORT_NO_ASSOCIATED_EXPERIMENT.value,
                                      GWSException.REPORT_NO_ASSOCIATED_EXPERIMENT.name)

        experiment_ids = [experiment.id for experiment in experiments]

        # retrieve the resources associated with the experiments
        resources = ResourceService.get_experiments_resources(experiment_ids)
        return resources

    @classmethod
    def _refresh_report_associated_resources(cls, report: Report) -> None:
        """Method to refresh the associated resources of a report. It will remove unassociated resources and
        add the new ones.
        """

        report_resources: List[ReportResourceModel] = ReportResourceModel.get_by_report(report.id)

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
                ReportResourceModel(report=report,
                                    resource=ResourceModel(id=content_resource)).save()

    ################################################# ARCHIVE ########################################

    @classmethod
    @transaction()
    def archive_report(cls, report_id: str) -> Report:
        report: Report = Report.get_by_id_and_check(report_id)

        if report.is_archived:
            raise BadRequestException('The report is already archived')

        ActivityService.add(
            ActivityType.ARCHIVE,
            object_type=ActivityObjectType.REPORT,
            object_id=report_id
        )
        return report.archive(True)

    @classmethod
    @transaction()
    def unarchive_report(cls, report_id: str) -> Report:
        report: Report = Report.get_by_id_and_check(report_id)

        if not report.is_archived:
            raise BadRequestException('The report is not archived')

        ActivityService.add(
            ActivityType.UNARCHIVE,
            object_type=ActivityObjectType.REPORT,
            object_id=report_id
        )
        return report.archive(False)
