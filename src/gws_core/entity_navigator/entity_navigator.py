# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from enum import Enum
from typing import List, Set, Type, Union

from gws_core.core.model.model import Model
from gws_core.experiment.experiment import Experiment
from gws_core.report.report import Report, ReportExperiment
from gws_core.report.report_view_model import ReportViewModel
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.task.task_input_model import TaskInputModel
from gws_core.task.task_model import TaskModel


class EntityType(Enum):
    EXPERIMENT = "EXPERIMENT"
    RESOURCE = "RESOURCE"
    VIEW = "VIEW"
    REPORT = "REPORT"


class EntityNavigator:

    _entities: Set[Model]

    def __init__(self, entities:  Union[Model, List[Model], Set[Model]]):
        if isinstance(entities, list):
            self._entities = set(entities)
        elif isinstance(entities, set):
            self._entities = entities
        else:
            self._entities = set([entities])

    def has_next_entities(self, requested_entities: List[EntityType] = None) -> bool:
        if requested_entities is None:
            requested_entities = [EntityType.EXPERIMENT, EntityType.RESOURCE,
                                  EntityType.REPORT, EntityType.VIEW]
        return len(self.get_next_entities(requested_entities)) > 0

    def get_next_entities(self, requested_entities: List[EntityType]) -> Set[Model]:
        """Return all the entities that are linked to the current entities

        :param requested_entities: [description]
        :type requested_entities: List[EntityType]
        :return: [description]
        :rtype: List[Model]
        """
        if self.is_empty():
            return set()

        next_entities = set()

        if EntityType.EXPERIMENT in requested_entities:
            next_entities.update(self.get_next_experiments().get_entities())

        if EntityType.RESOURCE in requested_entities:
            next_entities.update(self.get_next_resources().get_entities())

        if EntityType.REPORT in requested_entities:
            next_entities.update(self.get_next_reports().get_entities())

        if EntityType.VIEW in requested_entities:
            next_entities.update(self.get_next_views().get_entities())

        return next_entities

    def get_next_entities_recursive(self, requested_entities: List[EntityType]) -> Set[Model]:
        """Return all the entities that are linked to the current entities

        :param requested_entities: [description]
        :type requested_entities: List[EntityType]
        :return: [description]
        :rtype: List[Model]
        """
        if self.is_empty():
            return set()

        loaded_entities = set(self._entities)
        self._get_next_entities_recursive(requested_entities, loaded_entities)

        return loaded_entities - set(self._entities)

    def _get_next_entities_recursive(
            self, requested_entities: List[EntityType],
            loaded_entities: Set[Model]) -> Set[Model]:

        if self.is_empty():
            return loaded_entities

        if EntityType.EXPERIMENT in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities, loaded_entities, self.get_next_experiments(), EntityNavigatorExperiment)

        if EntityType.RESOURCE in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities, loaded_entities, self.get_next_resources(), EntityNavigatorResource)

        if EntityType.REPORT in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities, loaded_entities, self.get_next_reports(), EntityNavigatorReport)

        if EntityType.VIEW in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities, loaded_entities, self.get_next_views(), EntityNavigatorView)

        return loaded_entities

    def _get_next_entities_type_recursive(
            self, requested_entities: List[EntityType],
            loaded_entities: Set[Model],
            entity_nav: 'EntityNavigator',
            nav_class: Type['EntityNavigator']) -> Set[Model]:

        new_entities: Set[Experiment] = set(entity_nav.get_entities()) - set(loaded_entities)

        if len(new_entities) > 0:
            loaded_entities.update(new_entities)

            next_entity_nav: EntityNavigator = nav_class(new_entities)
            next_entity_nav._get_next_entities_recursive(requested_entities, loaded_entities)

        return loaded_entities

    def get_previous_entities_recursive(self, requested_entities: List[EntityType]) -> Set[Model]:
        """Return all the entities that are linked to the current entities

        :param requested_entities: [description]
        :type requested_entities: List[EntityType]
        :return: [description]
        :rtype: List[Model]
        """
        if self.is_empty():
            return set()

        loaded_entities = set(self._entities)
        self._get_previous_entities_recursive(requested_entities, loaded_entities)

        return loaded_entities - set(self._entities)

    def _get_previous_entities_recursive(
            self, requested_entities: List[EntityType],
            loaded_entities: Set[Model]) -> Set[Model]:

        if self.is_empty():
            return loaded_entities

        if EntityType.EXPERIMENT in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities, loaded_entities, self.get_previous_experiments(), EntityNavigatorExperiment)

        if EntityType.RESOURCE in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities, loaded_entities, self.get_previous_resources(), EntityNavigatorResource)

        if EntityType.REPORT in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities, loaded_entities, self.get_previous_reports(), EntityNavigatorReport)

        if EntityType.VIEW in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities, loaded_entities, self.get_previous_views(), EntityNavigatorView)

        return loaded_entities

    def _get_previous_entities_type_recursive(
            self, requested_entities: List[EntityType],
            loaded_entities: Set[Model],
            entity_nav: 'EntityNavigator',
            nav_class: Type['EntityNavigator']) -> Set[Model]:

        new_entities: Set[Experiment] = set(entity_nav.get_entities()) - set(loaded_entities)

        if len(new_entities) > 0:
            loaded_entities.update(new_entities)

            previous_entity_nav: EntityNavigator = nav_class(new_entities)
            previous_entity_nav._get_previous_entities_recursive(requested_entities, loaded_entities)

        return loaded_entities

    def get_next_reports(self) -> 'EntityNavigatorReport':
        return EntityNavigatorReport(set())

    def get_next_views(self) -> 'EntityNavigatorView':
        return EntityNavigatorView(set())

    def get_next_resources(self) -> 'EntityNavigatorResource':
        return EntityNavigatorResource(set())

    def get_next_experiments(self) -> 'EntityNavigatorExperiment':
        return EntityNavigatorExperiment(set())

    def get_previous_reports(self) -> 'EntityNavigatorReport':
        return EntityNavigatorReport(set())

    def get_previous_views(self) -> 'EntityNavigatorView':
        return EntityNavigatorView(set())

    def get_previous_resources(self) -> 'EntityNavigatorResource':
        return EntityNavigatorResource(set())

    def get_previous_experiments(self) -> 'EntityNavigatorExperiment':
        return EntityNavigatorExperiment(set())

    def get_entities(self) -> Set[Model]:
        return self._entities

    def get_entities_list(self) -> List[Model]:
        return list(self._entities)

    def is_empty(self) -> bool:
        return len(self._entities) == 0

    def _get_entities_ids(self) -> List[str]:
        return [entity.id for entity in self._entities]

    @classmethod
    def from_entity_id(cls, entity_type: EntityType, entity_id: str) -> 'EntityNavigator':
        if entity_type == EntityType.EXPERIMENT:
            return EntityNavigatorExperiment(Experiment.get_by_id_and_check(entity_id))
        elif entity_type == EntityType.REPORT:
            return EntityNavigatorView(Report.get_by_id_and_check(entity_id))
        elif entity_type == EntityType.VIEW:
            return EntityNavigatorReport(ViewConfig.get_by_id_and_check(entity_id))
        elif entity_type == EntityType.RESOURCE:
            return EntityNavigatorResource(ResourceModel.get_by_id_and_check(entity_id))

        raise Exception(f"Entity type {entity_type} not supported")


class EntityNavigatorExperiment(EntityNavigator):

    _entities: Set[Experiment]

    def get_next_reports(self) -> 'EntityNavigatorReport':
        reports = set(ReportExperiment.find_reports_by_experiments(self._get_entities_ids()))
        return EntityNavigatorReport(reports)

    def get_next_views(self) -> 'EntityNavigatorView':
        return self.get_next_resources().get_next_views()

    def get_next_resources(self) -> 'EntityNavigatorResource':
        """Return all the resources generated by the experiments"""
        resources = set(ResourceModel.get_by_experiments(self._get_entities_ids()))
        return EntityNavigatorResource(resources)

    def get_next_experiments(self) -> 'EntityNavigatorExperiment':
        return self.get_next_resources().get_next_experiments()

    def get_previous_resources(self) -> 'EntityNavigatorResource':
        task_models: List[TaskModel] = list(TaskModel.get_experiment_source_tasks(self._get_entities_ids()))

        resource_ids: List[str] = [task.source_config_id for task in task_models if task.source_config_id is not None]

        return EntityNavigatorResource(ResourceModel.get_by_ids(resource_ids))

    def get_previous_experiments(self) -> 'EntityNavigatorExperiment':
        return self.get_previous_resources().get_previous_experiments()


class EntityNavigatorResource(EntityNavigator):

    _entities: Set[ResourceModel]

    def get_next_reports(self) -> 'EntityNavigatorReport':
        return self.get_next_views().get_next_reports()

    def get_next_views(self) -> 'EntityNavigatorView':
        views = set(ViewConfig.get_by_resources(self._get_entities_ids()))
        return EntityNavigatorView(views)

    def get_next_resources(self) -> 'EntityNavigatorResource':
        tasks_model = self._get_next_tasks()

        task_model_ids = [task.id for task in tasks_model]

        resources = set(ResourceModel.get_by_task_models(task_model_ids))

        return EntityNavigatorResource(resources)

    def _get_next_tasks(self) -> Set[TaskModel]:
        # retrieve all the tasks that uses the resource as input
        # Don't retrieve the Source task that uses this resource as Config because the output of the Source task
        # is the resource itself
        task_input_models: List[TaskInputModel] = set(TaskInputModel.get_by_resource_models(self._get_entities_ids()))
        return {task_input.task_model for task_input in task_input_models}

    def get_next_experiments(self) -> 'EntityNavigatorExperiment':
        """Return all the experiments that use the resource as input of a task"""
        task_models: List[TaskModel] = list(TaskModel.get_source_task_using_resource_in_another_experiment(
            self._get_entities_ids()))

        experiments: Set[Experiment] = {task.experiment for task in task_models}

        return EntityNavigatorExperiment(experiments)

    def get_previous_resources(self) -> 'EntityNavigatorResource':
        # retrieve the tasks that generated the current resources
        task_model_ids = [resource.task_model.id for resource in self._entities if resource.task_model is not None]

        # retrieve all the inputs of the tasks
        task_input_model: List[TaskInputModel] = list(TaskInputModel.get_by_task_models(task_model_ids))

        resources = {task_input.resource_model for task_input in task_input_model}

        return EntityNavigatorResource(resources)

    def get_previous_experiments(self) -> 'EntityNavigatorExperiment':
        """ Return all the experiments that generated the current resources"""

        experiment_ids: List[str] = [resource.experiment.id for resource in self._entities
                                     if resource.experiment is not None]

        experiments = set(Experiment.get_by_ids(experiment_ids))

        return EntityNavigatorExperiment(experiments)


class EntityNavigatorView(EntityNavigator):

    _entities: Set[ViewConfig]

    def get_next_reports(self) -> 'EntityNavigatorReport':

        report_views: List[ReportViewModel] = list(ReportViewModel.get_by_views(self._get_entities_ids()))

        reports = set([report_view.report for report_view in report_views])

        return EntityNavigatorReport(reports)

    def get_previous_resources(self) -> 'EntityNavigatorResource':
        resource_ids: List[str] = [view.resource_model.id for view in self._entities if view.resource_model is not None]

        resources = set(ResourceModel.get_by_ids(resource_ids))

        return EntityNavigatorResource(resources)

    def get_previous_experiments(self) -> 'EntityNavigatorExperiment':
        return self.get_previous_resources().get_previous_experiments()

    def _get_resources(self) -> List[ResourceModel]:
        return [view.resource_model for view in self._entities]


class EntityNavigatorReport(EntityNavigator):

    _entities: Set[Report]

    def get_previous_views(self) -> 'EntityNavigatorView':
        report_views: List[ReportViewModel] = list(ReportViewModel.get_by_reports(self._get_entities_ids()))

        return EntityNavigatorView({report_view.view for report_view in report_views})

    def get_previous_resources(self) -> 'EntityNavigatorResource':
        return self.get_previous_views().get_previous_resources()

    def get_previous_experiments(self) -> 'EntityNavigatorExperiment':
        return self.get_previous_resources().get_previous_experiments()
