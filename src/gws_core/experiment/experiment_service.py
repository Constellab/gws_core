# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List, Optional, Type

from peewee import ModelSelect

from gws_core.core.classes.expression_builder import ExpressionBuilder
from gws_core.core.utils.date_helper import DateHelper
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.protocol_template.protocol_template import ProtocolTemplate
from gws_core.resource.resource_model import ResourceModel
from gws_core.task.task_input_model import TaskInputModel

from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import SearchBuilder, SearchParams
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
from ..core.service.base_service import BaseService
from ..experiment.experiment_search_builder import ExperimentSearchBuilder
from ..process.process_factory import ProcessFactory
from ..project.project import Project
from ..protocol.protocol import Protocol
from ..protocol.protocol_model import ProtocolModel
from ..protocol.protocol_service import ProtocolService
from ..space.space_dto import SaveExperimentToSpaceDTO
from ..space.space_service import SpaceService
from ..task.task_model import TaskModel
from ..user.activity.activity import ActivityObjectType, ActivityType
from ..user.activity.activity_service import ActivityService
from ..user.current_user_service import CurrentUserService
from .experiment import Experiment
from .experiment_dto import (ExperimentSaveDTO, RunningExperimentInfoDTO,
                             RunningProcessInfo)
from .experiment_enums import ExperimentStatus, ExperimentType


class ExperimentService(BaseService):

    ################################### CREATE ##############################

    @classmethod
    @transaction()
    def create_experiment_from_dto(cls, experiment_DTO: ExperimentSaveDTO) -> Experiment:

        protocol_template: ProtocolTemplate = None
        if experiment_DTO.protocol_template_id:
            protocol_template = ProtocolTemplate.get_by_id_and_check(
                experiment_DTO.protocol_template_id)
        elif experiment_DTO.protocol_template_json and isinstance(experiment_DTO.protocol_template_json, dict):
            protocol_template = ProtocolTemplate.from_json(
                experiment_DTO.protocol_template_json)

        return cls.create_experiment(
            project_id=experiment_DTO.project_id,
            title=experiment_DTO.title,
            protocol_template=protocol_template,
        )

    @classmethod
    @transaction()
    def create_experiment(cls, project_id: str = None, title: str = "",
                          protocol_template: ProtocolTemplate = None,
                          type_: ExperimentType = ExperimentType.EXPERIMENT) -> Experiment:
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
            type_=type_
        )

        ActivityService.add(
            ActivityType.CREATE,
            object_type=ActivityObjectType.EXPERIMENT,
            object_id=experiment.id
        )

        return experiment

    @classmethod
    @transaction()
    def create_experiment_from_protocol_model(
            cls, protocol_model: ProtocolModel, project: Project = None, title: str = "",
            description: Dict = None,
            type_: ExperimentType = ExperimentType.EXPERIMENT) -> Experiment:
        if not isinstance(protocol_model, ProtocolModel):
            raise BadRequestException(
                "An instance of ProtocolModel is required")
        experiment = Experiment()
        experiment.title = title.strip()
        experiment.description = description
        experiment.project = project
        experiment.type = type_

        experiment = experiment.save()

        # Set the experiment for the protocol_model and childs and save them
        protocol_model.set_experiment(experiment)
        protocol_model.save_full()
        return experiment

    @classmethod
    def create_experiment_from_protocol_type(
            cls, protocol_type: Type[Protocol],
            project: Project = None, title: str = "",
            type_: ExperimentType = ExperimentType.EXPERIMENT) -> Experiment:

        protocol_model: ProtocolModel = ProtocolService.create_protocol_model_from_type(
            protocol_type=protocol_type)
        return cls.create_experiment_from_protocol_model(
            protocol_model=protocol_model, project=project, title=title, type_=type_)

    ################################### UPDATE ##############################

    @classmethod
    def update_experiment(cls, experiment_id: str, experiment_dto: ExperimentSaveDTO) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

        experiment.check_is_updatable()

        experiment.title = experiment_dto.title.strip()

        return cls._update_experiment_project(experiment, experiment_dto.project_id)

    @classmethod
    def update_experiment_title(cls, experiment_id: str, title: str) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

        experiment.check_is_updatable()

        experiment.title = title.strip()

        return experiment.save()

    @classmethod
    def update_experiment_project(cls, experiment_id: str, project_id: Optional[str]) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

        experiment.check_is_updatable()

        return cls._update_experiment_project(experiment, project_id)

    @classmethod
    @transaction()
    def _update_experiment_project(cls, experiment: Experiment, new_project_id: Optional[str]) -> Experiment:
        project_changed = False
        project_removed = False

        new_project: Project = None
        # update the project
        if new_project_id:
            new_project = Project.get_by_id_and_check(new_project_id)

            if experiment.last_sync_at is not None and new_project != experiment.project:
                raise BadRequestException(
                    "You can't change the project of an experiment that has been synced")

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
            experiment.project = None
            if experiment.last_sync_at is not None:
                # delete the experiment in space
                SpaceService.delete_experiment(
                    project_id=experiment.project.id, experiment_id=experiment.id)

        return experiment

    @classmethod
    def update_experiment_description(cls, id: str, description: Dict) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)

        experiment.check_is_updatable()
        experiment.description = description
        return experiment.save()

    @classmethod
    def reset_experiment(cls, id: str) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)

        return experiment.reset()

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
        save_experiment_dto: SaveExperimentToSpaceDTO = {
            "experiment": experiment.to_json(),
            "protocol": experiment.export_protocol(),
            "lab_config": lab_config.to_json()
        }
        # Save the experiment in space
        SpaceService.save_experiment(
            experiment.project.id, save_experiment_dto)
        return experiment

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
    def get_experiment_by_id(cls, id: str) -> Experiment:
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
    def get_by_input_resource(cls, resource_id: str,
                              page: int = 0,
                              number_of_items_per_page: int = 20) -> Paginator[Experiment]:
        """ Return the list of experiment that used the resource as input

        :param resource_id: _description_
        :type resource_id: str
        :return: _description_
        :rtype: Paginator[Experiment]
        """

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(
            resource_id)

        expression_builder = ExpressionBuilder(
            TaskInputModel.resource_model == resource_id)

        # if the resource was generacted by an experiment, skip this experiment in the result
        if resource_model.experiment is not None:
            expression_builder.add_expression(
                Experiment.id != resource_model.experiment.id)

        query = Experiment.select().where(expression_builder.build()
                                          ).join(TaskInputModel).distinct()

        return Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_running_experiments(cls) -> List[RunningExperimentInfoDTO]:
        experiments: List[Experiment] = list(
            Experiment.select().where(Experiment.status == ExperimentStatus.RUNNING).order_by(
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
