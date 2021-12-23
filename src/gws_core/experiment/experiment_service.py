# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, Type

from peewee import ModelSelect

from ..central.central_service import CentralService
from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import SearchBuilder, SearchDict
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
from ..core.service.base_service import BaseService
from ..core.utils.logger import Logger
from ..core.utils.settings import Settings
from ..experiment.experiment_search_builder import ExperimentSearchBuilder
from ..process.process_factory import ProcessFactory
from ..project.project import Project
from ..project.project_dto import ProjectDto
from ..project.project_service import ProjectService
from ..protocol.protocol import Protocol
from ..protocol.protocol_model import ProtocolModel
from ..protocol.protocol_service import ProtocolService
from ..task.task import Task
from ..task.task_model import TaskModel
from ..task.task_service import TaskService
from ..user.activity import Activity
from ..user.activity_service import ActivityService
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from .experiment import Experiment, ExperimentType
from .experiment_dto import ExperimentDTO


class ExperimentService(BaseService):

    ################################### CREATE ##############################

    @classmethod
    def create_empty_experiment_from_dto(cls, experimentDTO: ExperimentDTO) -> Experiment:

        # retrieve the project
        project: Project = ProjectService.get_or_create_project_from_dto(experimentDTO.project)

        return cls.create_empty_experiment(
            project=project,
            title=experimentDTO.title,
        )

    @classmethod
    def create_empty_experiment(cls, project: Project = None, title: str = "",
                                type_: ExperimentType = ExperimentType.EXPERIMENT) -> Experiment:

        return cls.create_experiment_from_protocol_model(
            protocol_model=ProcessFactory.create_protocol_empty(),
            project=project,
            title=title,
            type_=type_
        )

    @classmethod
    @transaction()
    def create_experiment_from_task_model(
            cls, task_model: TaskModel, project: Project = None, title: str = "",
            type_: ExperimentType = ExperimentType.EXPERIMENT) -> Experiment:
        if not isinstance(task_model, TaskModel, ):
            raise BadRequestException("An instance of TaskModel is required")
        proto = ProtocolService.create_protocol_model_from_task_model(task_model=task_model)
        return cls.create_experiment_from_protocol_model(
            protocol_model=proto, project=project, title=title, type_=type_)

    @classmethod
    @transaction()
    def create_experiment_from_protocol_model(
            cls, protocol_model: ProtocolModel, project: Project = None, title: str = "",
            type_: ExperimentType = ExperimentType.EXPERIMENT) -> Experiment:
        if not isinstance(protocol_model, ProtocolModel):
            raise BadRequestException("An instance of ProtocolModel is required")
        experiment = Experiment()
        experiment.title = title
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

        protocol_model: ProtocolModel = ProtocolService.create_protocol_model_from_type(protocol_type=protocol_type)
        return cls.create_experiment_from_protocol_model(
            protocol_model=protocol_model, project=project, title=title, type_=type_)

    @classmethod
    def create_experiment_from_task_type(
            cls, task_type: Type[Task], project: Project = None, title: str = "",
            type_: ExperimentType = ExperimentType.EXPERIMENT) -> Experiment:

        task_model: TaskModel = TaskService.create_task_model_from_type(task_type=task_type)
        return cls.create_experiment_from_task_model(
            task_model=task_model, project=project, title=title, type_=type_)

    ################################### UPDATE ##############################

    @classmethod
    def update_experiment(cls, id, experiment_DTO: ExperimentDTO) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)

        experiment.check_is_updatable()

        experiment.title = experiment_DTO.title
        experiment.project = ProjectService.get_or_create_project_from_dto(experiment_DTO.project)

        experiment.save()
        return experiment

    @classmethod
    def update_experiment_protocol(cls, id: str, protocol_graph: Dict) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)

        experiment.check_is_updatable()
        ProtocolService.update_protocol_graph(protocol_model=experiment.protocol_model, graph=protocol_graph)

        experiment.save()
        return experiment

    @classmethod
    def update_experiment_description(cls, id: str, description: Dict) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)

        experiment.check_is_updatable()
        experiment.description = description
        return experiment.save()

    @classmethod
    @transaction()
    def validate_experiment(cls, id: str, project_dto: ProjectDto = None) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)

        # set the project if it is provided
        if project_dto is not None:
            experiment.project = ProjectService.get_or_create_project_from_dto(project_dto)

        experiment.validate()

        user: User = CurrentUserService.get_and_check_current_user()
        ActivityService.add(Activity.VALIDATE_EXPERIMENT,
                            object_type=Experiment.full_classname(),
                            object_id=experiment.id,
                            user=user)

        return experiment

    @classmethod
    @transaction()
    def validate_experiment_send_to_central(cls, id: str, project_dto: ProjectDto = None) -> Experiment:
        experiment = cls.validate_experiment(id, project_dto)

        # if Settings.is_local_env():
        #     Logger.info('Skipping sending experiment to central as we are running in LOCAL')
        #     return experiment

        # Save the experiment in central
        CentralService.save_experiment(experiment.project.id, experiment.to_json())

        return experiment

    ################################### GET  ##############################

    @classmethod
    def count_of_running_experiments(cls) -> int:
        """
        :return: the count of experiment in progress or waiting for a cli process
        :rtype: `int`
        """

        return Experiment.count_of_running_experiments()

    @classmethod
    def get_experiment_by_id(cls, id: str) -> Experiment:
        return Experiment.get_by_id_and_check(id)

    @classmethod
    def fetch_experiment_list(cls,
                              page: int = 0,
                              number_of_items_per_page: int = 20) -> Paginator[Experiment]:

        number_of_items_per_page = cls.get_number_of_item_per_page(
            number_of_items_per_page)

        query = Experiment.select().order_by(Experiment.created_at.desc())

        paginator: Paginator[Experiment] = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        return paginator

    @classmethod
    def search(cls,
               search: SearchDict,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[Experiment]:

        search_builder: SearchBuilder = ExperimentSearchBuilder()

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, number_of_items_per_page=number_of_items_per_page)

    ################################### COPY  ##############################

    @classmethod
    @transaction()
    def clone_experiment(cls, experiment_id: str) -> Experiment:
        """ Copy the experiment into a new draft experiment
        """
        experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

        new_experiment: Experiment = cls.create_experiment_from_protocol_model(
            protocol_model=ProtocolService.copy_protocol(experiment.protocol_model),
            project=experiment.project,
            title=experiment.title + " copy",
        )

        new_experiment.description = experiment.description
        return new_experiment.save()
