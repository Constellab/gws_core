

from typing import Dict, List, Optional, Type

from peewee import ModelSelect

from gws_core.core.utils.date_helper import DateHelper
from gws_core.entity_navigator.entity_navigator import EntityNavigatorResource
from gws_core.experiment.experiment_zipper import (ZipExperiment,
                                                   ZipExperimentInfo)
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.protocol_template.protocol_template import ProtocolTemplate
from gws_core.protocol_template.protocol_template_factory import \
    ProtocolTemplateFactory
from gws_core.report.report import ReportExperiment
from gws_core.resource.resource_model import ResourceModel
from gws_core.task.plug import Sink
from gws_core.task.task_input_model import TaskInputModel
from gws_core.user.activity.activity_dto import (ActivityObjectType,
                                                 ActivityType)
from gws_core.user.activity.activity_service import ActivityService

from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import SearchBuilder, SearchParams
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
from ..experiment.experiment_search_builder import ExperimentSearchBuilder
from ..process.process_factory import ProcessFactory
from ..project.project import Project
from ..protocol.protocol import Protocol
from ..protocol.protocol_model import ProtocolModel
from ..protocol.protocol_service import ProtocolService
from ..space.space_dto import SaveExperimentToSpaceDTO
from ..space.space_service import SpaceService
from ..task.task_model import TaskModel
from ..user.current_user_service import CurrentUserService
from .experiment import Experiment
from .experiment_dto import (ExperimentSaveDTO, RunningExperimentInfoDTO,
                             RunningProcessInfo)
from .experiment_enums import ExperimentCreationType, ExperimentStatus


class ExperimentService():

    ################################### CREATE ##############################

    @classmethod
    @transaction()
    def create_experiment_from_dto(cls, experiment_dto: ExperimentSaveDTO) -> Experiment:

        protocol_template: ProtocolTemplate = None
        if experiment_dto.protocol_template_id:
            protocol_template = ProtocolTemplate.get_by_id_and_check(
                experiment_dto.protocol_template_id)
        elif experiment_dto.protocol_template_json and isinstance(experiment_dto.protocol_template_json, dict):
            protocol_template = ProtocolTemplateFactory.from_export_dto_dict(
                experiment_dto.protocol_template_json)

        return cls.create_experiment(
            project_id=experiment_dto.project_id,
            title=experiment_dto.title,
            protocol_template=protocol_template,
            creation_type=ExperimentCreationType.MANUAL
        )

    @classmethod
    @transaction()
    def create_experiment(cls, project_id: str = None, title: str = "",
                          protocol_template: ProtocolTemplate = None,
                          creation_type: ExperimentCreationType = ExperimentCreationType.MANUAL) -> Experiment:
        protocol_model: ProtocolModel = None

        description: Dict = None
        if protocol_template is not None:
            description = protocol_template.description
            protocol_model = ProtocolService.create_protocol_model_from_template(protocol_template)
        else:
            protocol_model = ProcessFactory.create_protocol_empty()

        project = Project.get_by_id_and_check(project_id) if project_id else None

        experiment = cls.create_experiment_from_protocol_model(
            protocol_model=protocol_model,
            project=project,
            title=title,
            description=description,
            creation_type=creation_type
        )

        ActivityService .add(
            ActivityType.CREATE,
            object_type=ActivityObjectType.EXPERIMENT,
            object_id=experiment.id
        )

        return experiment

    @classmethod
    @transaction()
    def create_experiment_from_protocol_model(
            cls, protocol_model: ProtocolModel, project: Project = None, title: str = "", description: Dict = None,
            creation_type: ExperimentCreationType = ExperimentCreationType.MANUAL) -> Experiment:
        if not isinstance(protocol_model, ProtocolModel):
            raise BadRequestException(
                "An instance of ProtocolModel is required")
        experiment = Experiment()
        experiment.title = title.strip()
        experiment.description = description
        experiment.project = project
        experiment.creation_type = creation_type

        experiment = experiment.save()

        # Set the experiment for the protocol_model and childs and save them
        protocol_model.set_experiment(experiment)
        protocol_model.save_full()
        return experiment

    @classmethod
    def create_experiment_from_protocol_type(
            cls, protocol_type: Type[Protocol],
            project: Project = None, title: str = "", creation_type: ExperimentCreationType = ExperimentCreationType.
            MANUAL) -> Experiment:

        protocol_model: ProtocolModel = ProtocolService.create_protocol_model_from_type(
            protocol_type=protocol_type)
        return cls.create_experiment_from_protocol_model(
            protocol_model=protocol_model, project=project, title=title, creation_type=creation_type)

    ################################### UPDATE ##############################

    @classmethod
    def update_experiment_title(cls, experiment_id: str, title: str) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

        experiment.check_is_updatable()
        experiment.title = title.strip()
        experiment = experiment.save()

        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.EXPERIMENT,
                                            object_id=experiment.id)

        return experiment

    @classmethod
    def update_experiment_project(cls, experiment_id: str, project_id: Optional[str],
                                  check_report: bool = True) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

        experiment.check_is_updatable()

        experiment = cls._update_experiment_project(experiment, project_id, check_reports=check_report)

        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.EXPERIMENT,
                                            object_id=experiment.id)

        return experiment

    @classmethod
    @transaction()
    def _update_experiment_project(cls, experiment: Experiment,
                                   new_project_id: Optional[str],
                                   check_reports: bool) -> Experiment:
        project_changed = False
        project_removed = False
        old_project: Project = experiment.project

        new_project: Project = None
        # update the project
        if new_project_id:
            new_project = Project.get_by_id_and_check(new_project_id)

            if experiment.last_sync_at is not None and new_project != experiment.project:
                raise BadRequestException(
                    "You can't change the project of an experiment that has been synced. Please unlink the experiment from the project first.")

            if experiment.project != new_project:
                project_changed = True

        if experiment.project is not None and new_project_id is None:
            project_removed = True

        experiment.project = new_project

        # update experiment
        experiment = experiment.save()

        # update generated resources project
        if project_changed or project_removed:
            resources: List[ResourceModel] = ResourceModel.get_by_experiment(
                experiment.id)
            for resource in resources:
                resource.project = experiment.project
                resource.save()

        # if the project was removed
        if project_removed:
            if experiment.last_sync_at is not None:
                cls._unsynchronize_with_space(experiment, old_project.id,
                                              check_reports=check_reports)

        return experiment

    @classmethod
    def update_experiment_description(cls, id_: str, description: Dict) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id_)

        experiment.check_is_updatable()
        experiment.description = description
        experiment = experiment.save()

        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.EXPERIMENT,
                                            object_id=experiment.id)

        return experiment

    @classmethod
    def reset_experiment(cls, experiment: Experiment) -> Experiment:
        experiment = experiment.reset()

        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.EXPERIMENT,
                                            object_id=experiment.id)

        return experiment

    ###################################  VALIDATION  ##############################

    @classmethod
    @transaction()
    def validate_experiment_by_id(cls, id: str, project_id: str = None) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)

        # set the project if it is provided
        if project_id is not None:
            experiment.project = Project.get_by_id_and_check(project_id)

        return cls.validate_experiment(experiment)

    @classmethod
    @transaction()
    def validate_experiment(cls, experiment: Experiment) -> Experiment:
        experiment.validate()

        ActivityService.add(ActivityType.VALIDATE,
                            object_type=ActivityObjectType.EXPERIMENT,
                            object_id=experiment.id)

        # send the experiment to the space
        cls._synchronize_with_space(experiment)

        return experiment.save()

    ###################################  SYNCHRO WITH SPACE  ##############################

    @classmethod
    def synchronize_with_space_by_id(cls, id: str) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)
        experiment = cls._synchronize_with_space(experiment)
        return experiment.save()

    @classmethod
    def _synchronize_with_space(cls, experiment: Experiment) -> Experiment:
        # if Settings.is_local_env():
        #     Logger.info('Skipping sending experiment to space as we are running in LOCAL')
        #     return experiment

        if experiment.project is None:
            raise BadRequestException(
                "The experiment must be linked to a project before validating it")

        experiment.last_sync_at = DateHelper.now_utc()
        experiment.last_sync_by = CurrentUserService.get_and_check_current_user()

        lab_config: LabConfigModel = experiment.lab_config
        if lab_config is None:
            lab_config = LabConfigModel.get_current_config()
        save_experiment_dto = SaveExperimentToSpaceDTO(
            experiment=experiment.to_dto(),
            protocol=experiment.export_protocol(),
            lab_config=lab_config.to_dto()
        )
        # Save the experiment in space
        SpaceService.save_experiment(
            experiment.project.id, save_experiment_dto)
        return experiment

    @classmethod
    @transaction()
    def _unsynchronize_with_space(cls, experiment: Experiment, project_id: str,
                                  check_reports: bool) -> Experiment:

        if check_reports:
            synced_associated_reports = ReportExperiment.find_synced_reports_by_experiment(experiment.id)

            if len(synced_associated_reports) > 0:
                raise BadRequestException(
                    "You can't unsynchronize an experiment that has associated reports synced in space. Please unsync the reports first.")

        # Delete the experiment in space
        SpaceService.delete_experiment(project_id, experiment.id)

        # clear sync info
        experiment.last_sync_at = None
        experiment.last_sync_by = None
        return experiment.save()

    ################################### ARCHIVE  ##############################

    @classmethod
    @transaction()
    def archive_experiment_by_id(cls, id: str) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)

        if experiment.is_archived:
            raise BadRequestException("The experiment is already archived")

        if experiment.is_running:
            raise BadRequestException("You can't archive an experiment that is running")

        ActivityService.add(
            ActivityType.ARCHIVE,
            object_type=ActivityObjectType.EXPERIMENT,
            object_id=id
        )

        return experiment.archive(archive=True)

    @classmethod
    def unarchive_experiment_by_id(cls, id: str) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)

        if not experiment.is_archived:
            raise BadRequestException("The experiment is not archived")

        ActivityService.add(
            ActivityType.UNARCHIVE,
            object_type=ActivityObjectType.EXPERIMENT,
            object_id=id
        )

        return experiment.archive(archive=False)

    ################################### GET  ##############################

    @classmethod
    def count_of_running_experiments(cls) -> int:
        """
        :return: the count of experiment in progress or waiting for a cli process
        :rtype: `int`
        """

        return Experiment.count_running_experiments()

    @classmethod
    def count_running_or_queued_experiments(cls) -> int:
        return Experiment.count_running_or_queued_experiments()

    @classmethod
    def count_queued_experiments(cls) -> int:
        return Experiment.count_queued_experiments()

    @classmethod
    def get_by_id_and_check(cls, id: str) -> Experiment:
        return Experiment.get_by_id_and_check(id)

    @classmethod
    def search(cls,
               search: SearchParams,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[Experiment]:

        search_builder: SearchBuilder = ExperimentSearchBuilder()

        model_select: ModelSelect = search_builder.add_search_params(search).build_search()
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def count_by_title(cls,
                       title: str) -> int:

        return Experiment.select().where(Experiment.title == title.strip()).count()

    @classmethod
    def search_by_title(cls,
                        title: str,
                        page: int = 0,
                        number_of_items_per_page: int = 20) -> Paginator[Experiment]:

        model_select: ModelSelect = Experiment.select().where(Experiment.title.contains(title))
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_next_experiments_of_resource(cls, resource_id: str,
                                         page: int = 0,
                                         number_of_items_per_page: int = 20) -> Paginator[Experiment]:
        """ Return the list of experiment that used the resource as input

        :param resource_id: _description_
        :type resource_id: str
        :return: _description_
        :rtype: Paginator[Experiment]
        """

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_id)

        resource_navigator = EntityNavigatorResource(resource_model)
        return Paginator(resource_navigator.get_next_experiments_select_model(),
                         page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_running_experiments(cls) -> List[RunningExperimentInfoDTO]:
        experiments: List[Experiment] = list(
            Experiment.select().where(
                # consider the WAITING_FOR_CLI_PROCESS as running
                Experiment.status.in_([ExperimentStatus.RUNNING, ExperimentStatus.WAITING_FOR_CLI_PROCESS])).order_by(
                Experiment.last_modified_at.desc()))

        return [cls.get_running_experiment_info(experiment) for experiment in experiments]

    @classmethod
    def get_running_experiment_info(cls, experiment: Experiment) -> RunningExperimentInfoDTO:
        tasks: List[TaskModel] = experiment.get_running_tasks()

        running_tasks: List[RunningProcessInfo] = []
        for task in tasks:
            running_task = RunningProcessInfo(id=task.id,
                                              title=task.get_name(),
                                              last_message=task.get_last_message(),
                                              progression=task.get_progress_value())
            running_tasks.append(running_task)

        return RunningExperimentInfoDTO(
            id=experiment.id,
            title=experiment.title,
            project=experiment.project.to_dto() if experiment.project else None,
            running_tasks=running_tasks,
        )

    ################################### COPY  ##############################

    @classmethod
    @transaction()
    def clone_experiment(cls, experiment_id: str) -> Experiment:
        """ Copy the experiment into a new draft experiment
        """
        experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

        new_experiment: Experiment = cls.create_experiment_from_protocol_model(
            protocol_model=ProtocolService.copy_protocol(
                experiment.protocol_model),
            project=experiment.project,
            title=experiment.title + " copy",
        )

        new_experiment.description = experiment.description
        return new_experiment.save()

    ################################### DELETE ##############################

    @classmethod
    @transaction()
    def delete_experiment(cls, experiment_id: str) -> None:

        experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

        experiment.delete_instance()

        # if the experiment was sync with space, delete it in space too
        if experiment.last_sync_at is not None and experiment.project is not None:
            SpaceService.delete_experiment(
                experiment.project.id, experiment.id)

        ActivityService.add(activity_type=ActivityType.DELETE,
                            object_type=ActivityObjectType.EXPERIMENT,
                            object_id=experiment.id)

    ################################### INTERMEDIATE RESOURCES ##############################

    @classmethod
    @transaction()
    def delete_intermediate_resources(cls, experiment_id: str) -> None:
        """Delete the intermediate resources of an experiment
        An intermediate resource is a resource that is not used as input of a sink and not flagged

        :param experiment_id: id of the experiment
        :type experiment_id: str
        """

        intermediate_resources: List[ResourceModel] = cls.get_intermediate_results(
            experiment_id)

        if not intermediate_resources:
            raise BadRequestException("No intermediate resources found for the experiment")

        # check if all the intermediate resources where already deleted
        if all(resource.content_is_deleted for resource in intermediate_resources):
            raise BadRequestException("All the intermediate resources are already deleted")

        # check if the intermediate resources are used in other experiments
        resoure_navigator = EntityNavigatorResource(intermediate_resources)
        if resoure_navigator.get_next_experiments().has_entities():
            raise BadRequestException(
                "Some intermediate resources are used in other experiments")

        # delete the intermediate resources content
        for resource in intermediate_resources:
            resource.delete_resource_content()

        ActivityService.add(activity_type=ActivityType.DELETE_EXPERIMENT_INTERMEDIATE_RESOURCES,
                            object_type=ActivityObjectType.EXPERIMENT,
                            object_id=experiment_id)

    @classmethod
    def get_intermediate_results(cls, experiment_id: str) -> List[ResourceModel]:
        """Retrieve the list of intermediate resources of an experiment
        A resource is considered as intermediate if it is not used as input of a sink and not flagged

        :param experiment_id: id of the experiment
        :type experiment_id: str
        :return: _description_
        :rtype: List[ResourceModel]
        """
        not_flagged_resources: List[ResourceModel] = list(
            ResourceModel.get_resource_by_experiment_and_flag(experiment_id, False)
        )

        intermediate_resources: List[ResourceModel] = []
        for resource in not_flagged_resources:
            # check if the resource is used a input of sink
            task_input_model = TaskInputModel.get_by_resource_model_and_task_type(
                resource.id, Sink.get_typing_name())

            # if the resource is not used as input of a sink, it is an intermediate resource
            if not task_input_model:
                intermediate_resources.append(resource)

        return intermediate_resources

    ################################### EXPORT / IMPORT ##############################

    @classmethod
    def export_experiment(cls, experiment_id: str) -> ZipExperimentInfo:
        experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

        experimeny_zip = ZipExperiment(
            id=experiment.id,
            title=experiment.title,
            description=experiment.description,
            status=experiment.status,
            project=experiment.project.to_dto() if experiment.project is not None else None,
            error_info=experiment.error_info
        )

        return ZipExperimentInfo(
            zip_version=1,
            experiment=experimeny_zip,
            protocol=experiment.export_protocol(),
        )
