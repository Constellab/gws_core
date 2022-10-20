# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List, Type

from gws_core.core.classes.expression_builder import ExpressionBuilder
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.resource.resource_model import ResourceModel
from gws_core.task.task_input_model import TaskInputModel
from peewee import ModelSelect

from ..central.central_dto import SaveExperimentToCentralDTO
from ..central.central_service import CentralService
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
from ..task.task import Task
from ..task.task_model import TaskModel
from ..task.task_service import TaskService
from ..user.activity import Activity
from ..user.activity_service import ActivityService
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from .experiment import Experiment
from .experiment_dto import ExperimentDTO
from .experiment_enums import ExperimentStatus, ExperimentType


class ExperimentService(BaseService):

    ################################### CREATE ##############################

    @classmethod
    def create_empty_experiment_from_dto(cls, experimentDTO: ExperimentDTO) -> Experiment:

        return cls.create_empty_experiment(
            project_id=experimentDTO.project_id,
            title=experimentDTO.title,
        )

    @classmethod
    def create_empty_experiment(cls, project_id: str = None, title: str = "",
                                type_: ExperimentType = ExperimentType.EXPERIMENT) -> Experiment:

        return cls.create_experiment_from_protocol_model(
            protocol_model=ProcessFactory.create_protocol_empty(),
            project=Project.get_by_id_and_check(project_id) if project_id else None,
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
    def update_experiment(cls, id: str, experiment_DTO: ExperimentDTO) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)

        experiment.check_is_updatable()

        experiment.title = experiment_DTO.title

        # update the project
        if experiment_DTO.project_id:
            project = Project.get_by_id_and_check(experiment_DTO.project_id)

            if experiment.last_sync_at is not None and project != experiment.project:
                raise BadRequestException("You can't change the project of an experiment that has been synced")
            experiment.project = project

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

        user: User = CurrentUserService.get_and_check_current_user()
        ActivityService.add(Activity.VALIDATE_EXPERIMENT,
                            object_type=Experiment.full_classname(),
                            object_id=experiment.id,
                            user=user)

        # send the experiment to the central
        cls._synchronize_with_central(experiment)

        return experiment.save()

    ###################################  SYNCHRO WITH CENTRAL  ##############################

    @classmethod
    def synchronize_with_central_by_id(cls, id: str) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)
        experiment = cls._synchronize_with_central(experiment)
        return experiment.save()

    @classmethod
    def _synchronize_with_central(cls, experiment: Experiment) -> Experiment:
        if Settings.is_local_env():
            Logger.info('Skipping sending experiment to central as we are running in LOCAL')
            return experiment

        if experiment.project is None:
            raise BadRequestException("The experiment must be linked to a project before validating it")

        experiment.last_sync_at = DateHelper.now_utc()
        experiment.last_sync_by = CurrentUserService.get_and_check_current_user()

        lab_config: LabConfigModel = experiment.lab_config
        if lab_config is None:
            lab_config = LabConfigModel.get_current_config()
        save_experiment_dto: SaveExperimentToCentralDTO = {
            "experiment": experiment.to_json(),
            "protocol": experiment.export_protocol(),
            "lab_config": lab_config.to_json()
        }
        # Save the experiment in central
        CentralService.save_experiment(experiment.project.id, save_experiment_dto)
        return experiment

    ################################### GET  ##############################

    @classmethod
    def count_of_running_experiments(cls) -> int:
        """
        :return: the count of experiment in progress or waiting for a cli process
        :rtype: `int`
        """

        return Experiment.count_running_experiments()

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
            query, page=page, nb_of_items_per_page=number_of_items_per_page)
        return paginator

    @classmethod
    def search(cls,
               search: SearchParams,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[Experiment]:

        search_builder: SearchBuilder = ExperimentSearchBuilder()

        model_select: ModelSelect = search_builder.build_search(search)
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

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_id)

        expression_builder = ExpressionBuilder(TaskInputModel.resource_model == resource_id)

        # if the resource was generacted by an experiment, skip this experiment in the result
        if resource_model.experiment is not None:
            expression_builder.add_expression(Experiment.id != resource_model.experiment.id)

        query = Experiment.select().where(expression_builder.build()).join(TaskInputModel).distinct()

        return Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_running_experiments(cls) -> List[Experiment]:
        return list(Experiment.select().where(Experiment.status == ExperimentStatus.RUNNING))

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

      ################################### DELETE ##############################

    @classmethod
    @transaction()
    def delete_experiment(cls, experiment_id: str) -> None:

        experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

        experiment.delete_instance()

        # if the experiment was sync with central, delete it in central too
        if experiment.last_sync_at is not None and experiment.project is not None:
            CentralService.delete_experiment(experiment.project.id, experiment.id)
