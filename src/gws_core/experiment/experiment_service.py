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
from ..protocol.protocol import Protocol
from ..protocol.protocol_model import ProtocolModel
from ..protocol.protocol_service import ProtocolService
from ..study.study import Study
from ..study.study_dto import StudyDto
from ..study.study_service import StudyService
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

        # retrieve the study
        study: Study = StudyService.get_or_create_study_from_dto(experimentDTO.study)

        return cls.create_empty_experiment(
            study=study,
            title=experimentDTO.title,
            description=experimentDTO.description,
        )

    @classmethod
    def create_empty_experiment(cls, study: Study = None, title: str = "", description: str = "",
                                type_: ExperimentType = ExperimentType.EXPERIMENT) -> Experiment:

        return cls.create_experiment_from_protocol_model(
            protocol_model=ProcessFactory.create_protocol_empty(),
            study=study,
            title=title,
            description=description,
            type_=type_
        )

    @classmethod
    @transaction()
    def create_experiment_from_task_model(
            cls, task_model: TaskModel, study: Study = None, title: str = "", description: str = "",
            type_: ExperimentType = ExperimentType.EXPERIMENT) -> Experiment:
        if not isinstance(task_model, TaskModel, ):
            raise BadRequestException("An instance of TaskModel is required")
        proto = ProtocolService.create_protocol_model_from_task_model(task_model=task_model)
        return cls.create_experiment_from_protocol_model(
            protocol_model=proto, study=study, title=title, description=description, type_=type_)

    @classmethod
    @transaction()
    def create_experiment_from_protocol_model(
            cls, protocol_model: ProtocolModel, study: Study = None, title: str = "", description: str = "",
            type_: ExperimentType = ExperimentType.EXPERIMENT) -> Experiment:
        if not isinstance(protocol_model, ProtocolModel):
            raise BadRequestException("An instance of ProtocolModel is required")
        experiment = Experiment()
        experiment.title = title
        experiment.description = description
        experiment.study = study
        experiment.type = type_

        experiment = experiment.save()

        # Set the experiment for the protocol_model and childs and save them
        protocol_model.set_experiment(experiment)
        protocol_model.save_full()
        return experiment

    @classmethod
    def create_experiment_from_protocol_type(
            cls, protocol_type: Type[Protocol],
            study: Study = None, title: str = "", description: str = "",
            type_: ExperimentType = ExperimentType.EXPERIMENT) -> Experiment:

        protocol_model: ProtocolModel = ProtocolService.create_protocol_model_from_type(protocol_type=protocol_type)
        return cls.create_experiment_from_protocol_model(
            protocol_model=protocol_model, study=study, title=title, description=description, type_=type_)

    @classmethod
    def create_experiment_from_task_type(
            cls, task_type: Type[Task], study: Study = None, title: str = "",
            description: str = "", type_: ExperimentType = ExperimentType.EXPERIMENT) -> Experiment:

        task_model: TaskModel = TaskService.create_task_model_from_type(task_type=task_type)
        return cls.create_experiment_from_task_model(
            task_model=task_model, study=study, title=title, description=description, type_=type_)

    ################################### UPDATE ##############################

    @classmethod
    def update_experiment(cls, id, experiment_DTO: ExperimentDTO) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)

        experiment.check_is_updatable()

        experiment.title = experiment_DTO.title
        experiment.description = experiment_DTO.description
        experiment.study = StudyService.get_or_create_study_from_dto(experiment_DTO.study)

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
    @transaction()
    def validate_experiment(cls, id: str, study_dto: StudyDto = None) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)

        # set the study if it is provided
        if study_dto is not None:
            experiment.study = StudyService.get_or_create_study_from_dto(study_dto)

        experiment.validate()

        user: User = CurrentUserService.get_and_check_current_user()
        ActivityService.add(Activity.VALIDATE_EXPERIMENT,
                            object_type=Experiment.full_classname(),
                            object_id=experiment.id,
                            user=user)

        return experiment

    @classmethod
    @transaction()
    def validate_experiment_send_to_central(cls, id: str, study_dto: StudyDto = None) -> Experiment:
        experiment = cls.validate_experiment(id, study_dto)

        if Settings.is_local_env():
            Logger.info('Skipping sending experiment to central as we are running in LOCAL')
            return experiment

        # Save the experiment in central
        CentralService.save_experiment(experiment.study.id, experiment.to_json())

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

        return cls.create_experiment_from_protocol_model(
            protocol_model=ProtocolService.copy_protocol(experiment.protocol_model),
            study=experiment.study,
            title=experiment.title + " copy",
            description=experiment.description
        )
