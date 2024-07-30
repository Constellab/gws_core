

from typing import Callable, List, Optional

from gws_core.core.utils.date_helper import DateHelper
from gws_core.document.document_dto import DocumentSaveDTO
from gws_core.document.document_service import DocumentService, DocumentType
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.impl.rich_text.rich_text_file_service import RichTextFileService
from gws_core.impl.rich_text.rich_text_types import (RichTextBlockType,
                                                     RichTextDTO,
                                                     RichTextObjectType,
                                                     RichTextResourceViewData,
                                                     RichTextViewFileData)
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.note.note import Note
from gws_core.project.project import Project
from gws_core.report.report_experiment import ReportExperiment
from gws_core.report.report_view_model import ReportViewModel
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view.view_types import exluded_views_in_report
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.resource.view_config.view_config_service import ViewConfigService
from gws_core.space.space_dto import (SaveReportToSpaceDTO,
                                      SpaceReportRichTextFileViewData)
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_dto import TagOriginType
from gws_core.task.task_input_model import TaskInputModel
from gws_core.user.activity.activity_dto import (ActivityObjectType,
                                                 ActivityType)
from gws_core.user.activity.activity_service import ActivityService
from gws_core.user.current_user_service import CurrentUserService

from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import SearchParams
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..experiment.experiment import Experiment
from ..space.space_service import SpaceService


class NoteService():

    @classmethod
    def get_document_service(cls) -> DocumentService:
        return DocumentService(DocumentType.NOTE,
                               Note, RichTextObjectType.NOTE,
                               ActivityObjectType.NOTE)

    @classmethod
    @transaction()
    def create(cls, note_dto: DocumentSaveDTO) -> Note:
        document_service = cls.get_document_service()

        return document_service.create(note_dto)

    @classmethod
    def update_title(cls, note_id: str, title: str) -> Note:
        document_service = cls.get_document_service()
        return document_service.update_title(note_id, title)

    @classmethod
    def update_project(cls, note_id: str, project_id: str) -> Note:
        document_service = cls.get_document_service()
        note: Note = document_service.get_and_check_before_update(note_id)

        note = cls._update_project(note, project_id)

        note = note.save()

        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.NOTE,
                                            object_id=note.id)

        return note

    @classmethod
    @transaction()
    def _update_project(cls, note: Note, project_id: Optional[str]) -> Note:
        # update project
        if project_id:
            project = Project.get_by_id_and_check(project_id)
            if note.last_sync_at is not None and project != note.project:
                raise BadRequestException(
                    "You can't change the project of a note that has been synced. You must unlink it from the project first.")
            note.project = project

        # if the project was removed
        if project_id is None and note.project is not None:

            if note.last_sync_at is not None:
                cls._unsynchronize_with_space(note, note.project.id)
            note.project = None

        return note

    @classmethod
    @transaction()
    def update_content(cls, note_id: str, note_content: RichTextDTO) -> Note:
        document_service = cls.get_document_service()
        note: Note = document_service.get_and_check_before_update(note_id)

        note.content = note_content

        note = note.save()
        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.NOTE,
                                            object_id=note.id)

        return note

    @classmethod
    def delete(cls, note_id: str) -> None:
        # delete the object in the database
        cls._delete_note_db(note_id)

        # if transaction is successful, delete the object in the file system
        RichTextFileService.delete_object_dir(RichTextObjectType.NOTE, note_id)

    @classmethod
    @transaction()
    def _delete_note_db(cls, note_id: str) -> None:
        document_service = cls.get_document_service()
        note: Note = document_service.get_and_check_before_update(note_id)

        Note.delete_by_id(note_id)
        EntityTagList.delete_by_entity(EntityType.NOTE, note_id)

        # if the note was sync with space, delete it in space too
        if note.last_sync_at is not None and note.project is not None:
            # TODO
            SpaceService.delete_report(note.project.id, note.id)

        ActivityService.add(ActivityType.DELETE,
                            object_type=ActivityObjectType.REPORT,
                            object_id=note_id)

    @classmethod
    @transaction()
    def _validate(cls, report_id: str, project_id: str = None) -> Report:
        document_service = cls.get_document_service()
        report: Report = document_service.get_and_check_before_update(report_id)

        rich_text = report.get_content_as_rich_text()
        if rich_text.is_empty():
            raise BadRequestException('The report is empty')

        # set the project if it is provided
        if project_id is not None:
            report.project = Project.get_by_id_and_check(project_id)

        if report.project is None:
            raise BadRequestException("The report must be associated to a project to be validated")

        if report.project.children.count() > 0:
            raise BadRequestException(
                "The report must be associated with a leaf project (project with no children)")

        # check that all linked experiment are validated and are in same project
        experiments: List[Experiment] = cls.get_experiments_by_report(report_id)
        for experiment in experiments:
            if experiment.project and experiment.project.id != report.project.id:
                raise BadRequestException(GWSException.REPORT_VALIDATION_EXP_OTHER_PROJECT.value,
                                          GWSException.REPORT_VALIDATION_EXP_OTHER_PROJECT.name, {'title': experiment.title})

        # refresh the associated resource (for precaution)
        cls._refresh_report_views_and_tags(report)
        # check that all resource views are from resource that
        # were generated by experiments that are linked to the report
        resource_views: List[RichTextResourceViewData] = rich_text.get_resource_views_data()
        experiment_ids = [experiment.id for experiment in experiments]
        for resource_view in resource_views:
            resource = ResourceService.get_by_id_and_check(resource_view["resource_id"])

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

        save_report_dto = SaveReportToSpaceDTO(
            report=report.to_full_dto(),
            experiment_ids=[experiment.id for experiment in experiments],
            lab_config=lab_config.to_dto(),
            resource_views={}
        )

        rich_text = report.get_content_as_rich_text()

        # retrieve all the figures file path
        file_paths: List[str] = []

        for figure in rich_text.get_figures_data():
            file_paths.append(RichTextFileService.get_figure_file_path(RichTextObjectType.REPORT, report.id,
                                                                       figure['filename']))

        for file in rich_text.get_files_data():
            file_paths.append(RichTextFileService.get_uploaded_file_path(RichTextObjectType.REPORT, report.id,
                                                                         file['name']))

        # set the resource views in the json object
        for resource_view in rich_text.get_resource_views_data():
            # set the json view in the resource_views object
            # with the view id as key
            view_result = ResourceService.get_and_call_view_on_resource_model(
                resource_view["resource_id"],
                resource_view["view_method_name"],
                resource_view["view_config"])
            save_report_dto.resource_views[resource_view["id"]] = view_result.to_dto()

        # set the file views in the json object
        for file_view_block in rich_text.get_blocks_by_type(RichTextBlockType.FILE_VIEW):

            data: RichTextViewFileData = file_view_block.data

            # retrieve the file view
            view_result_dto = RichTextFileService.get_file_view(RichTextObjectType.REPORT,
                                                                report.id,
                                                                data["filename"])
            save_report_dto.resource_views[data["id"]] = view_result_dto

            # replace the block info with the new data to have a simpler object in space
            new_data: SpaceReportRichTextFileViewData = {
                "id": data["id"],
                "title": data.get("title"),
                "caption": data.get("caption")
            }
            rich_text.replace_block_data_by_id(file_view_block.id, new_data)

        # Save the experiment in space
        SpaceService.save_report(report.project.id, save_report_dto, file_paths)

        return report

    @classmethod
    def _unsynchronize_with_space(cls, report: Report, project_id: str) -> Report:
        # delete the report in space
        SpaceService.delete_report(project_id=project_id, report_id=report.id)

        report.last_sync_at = None
        report.last_sync_by = None

        return report

    ###################################  LINKED EXPERIMENT  ##############################

    @classmethod
    @transaction()
    def add_experiment(cls, report_id: str, experiment_id: str,
                       error_if_already_linked: bool = True) -> Experiment:
        document_service = cls.get_document_service()
        report: Report = document_service.get_and_check_before_update(report_id)

        report_exp: ReportExperiment = ReportExperiment.find_by_pk(experiment_id, report_id).first()

        # If the experiment was already added to the report
        if report_exp is not None:

            if error_if_already_linked:
                raise BadRequestException(GWSException.REPORT_EXP_ALREADY_LINKED.value,
                                          GWSException.REPORT_EXP_ALREADY_LINKED.name)
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

        # add the experiment tags to the report
        experiment_tags = EntityTagList.find_by_entity(EntityType.EXPERIMENT, experiment.id)
        propagated_tags = experiment_tags.build_tags_propagated(TagOriginType.EXPERIMENT_PROPAGATED, experiment.id)
        report_tags = EntityTagList.find_by_entity(EntityType.REPORT, report.id)
        report_tags.add_tags(propagated_tags)

        return experiment

    @classmethod
    def remove_experiment(cls, report_id: str, experiment_id: str) -> None:
        document_service = cls.get_document_service()
        report: Report = document_service.get_and_check_before_update(report_id)

        rich_text = report.get_content_as_rich_text()
        report_views = rich_text.get_resource_views_data()

        # if any of the view is from the experiment, raise an error
        for report_view in report_views:
            if report_view.get('experiment_id') == experiment_id:
                raise BadRequestException(GWSException.REPORT_HAS_A_VIEW_FROM_EXPERIMENT.value,
                                          GWSException.REPORT_HAS_A_VIEW_FROM_EXPERIMENT.name)

        ReportExperiment.delete_obj(experiment_id, report_id)

        # remove the experiment tags from the report
        experiment_tags = EntityTagList.find_by_entity(EntityType.EXPERIMENT, experiment_id)
        propagated_tags = experiment_tags.build_tags_propagated(TagOriginType.EXPERIMENT_PROPAGATED, experiment_id)
        report_tags = EntityTagList.find_by_entity(EntityType.REPORT, report_id)
        report_tags.delete_tags(propagated_tags)

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
        document_service = cls.get_document_service()
        return document_service.search(search, page, number_of_items_per_page)

    @classmethod
    def search_by_name(cls, name: str,
                       page: int = 0,
                       number_of_items_per_page: int = 20) -> Paginator[Report]:
        document_service = cls.get_document_service()
        return document_service.search_by_name(name, page, number_of_items_per_page)

    @classmethod
    def get_by_resource(cls, resource_id: str,
                        page: int = 0,
                        number_of_items_per_page: int = 20) -> Paginator[Report]:

        query = ReportViewModel.get_by_resource(resource_id)

        paginator: Paginator[ReportViewModel] = Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)

        map_function: Callable[[ReportViewModel], Report] = lambda x: x.report
        paginator.map_result(map_function)
        return paginator

    ################################################# Resource View ########################################

    @classmethod
    def get_resources_of_associated_experiments(cls, report_id: str) -> List[ResourceModel]:
        """Method to retrieve the resources of the experiments associated with a report.
        Resources used as input or output of the experiments are returned.
        """
        # add a filter on experiments of the report
        experiments = ReportService.get_experiments_by_report(report_id)

        if len(experiments) == 0:
            raise BadRequestException(GWSException.REPORT_NO_LINKED_EXPERIMENT.value,
                                      GWSException.REPORT_NO_LINKED_EXPERIMENT.name)

        experiment_ids = [experiment.id for experiment in experiments]

        # retrieve the resources associated with the experiments
        resources = ResourceService.get_experiments_resources(experiment_ids)
        return resources

    ################################################# ARCHIVE ########################################

    @classmethod
    @transaction()
    def archive_report(cls, report_id: str) -> Report:
        document_service = cls.get_document_service()
        return document_service.archive(report_id)

    @classmethod
    @transaction()
    def unarchive_report(cls, report_id: str) -> Report:
        document_service = cls.get_document_service()
        return document_service.unarchive(report_id)
