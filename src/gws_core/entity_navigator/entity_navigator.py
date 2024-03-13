

from typing import Dict, Generic, Iterable, List, Set, Type, Union

from peewee import JOIN, ModelSelect

from gws_core.entity_navigator.entity_navigator_deep import NavigableEntitySet
from gws_core.entity_navigator.entity_navigator_type import (
    EntityType, GenericNavigableEntity, NavigableEntity, all_entity_types)
from gws_core.experiment.experiment import Experiment
from gws_core.report.report import Report, ReportExperiment
from gws_core.report.report_view_model import ReportViewModel
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag
from gws_core.tag.tag_dto import TagOriginType
from gws_core.task.task_input_model import TaskInputModel
from gws_core.task.task_model import TaskModel


class EntityNavigator(Generic[GenericNavigableEntity]):

    _entities: Set[GenericNavigableEntity]

    _all_entity_types = all_entity_types

    def __init__(self, entities: Union[GenericNavigableEntity, Iterable[GenericNavigableEntity]]):
        if entities is None:
            self._entities = set()
        elif isinstance(entities, Iterable):
            self._entities = set(entities)
        else:
            self._entities = set([entities])

    def has_next_entities(self, requested_entities: List[EntityType] = None) -> bool:
        if requested_entities is None:
            requested_entities = self._all_entity_types
        return len(self.get_next_entities(requested_entities)) > 0

    def get_next_entities(self, requested_entities: List[EntityType]) -> NavigableEntitySet:
        """Return all the entities that are linked to the current entities

        :param requested_entities: [description]
        :type requested_entities: List[EntityType]
        :return: [description]
        :rtype: NavigableEntitySet
        """
        if self.is_empty():
            return NavigableEntitySet()

        next_entities = set()

        if EntityType.EXPERIMENT in requested_entities:
            next_entities.update(self.get_next_experiments().get_entities_as_set())

        if EntityType.RESOURCE in requested_entities:
            next_entities.update(self.get_next_resources().get_entities_as_set())

        if EntityType.REPORT in requested_entities:
            next_entities.update(self.get_next_reports().get_entities_as_set())

        if EntityType.VIEW in requested_entities:
            next_entities.update(self.get_next_views().get_entities_as_set())

        return NavigableEntitySet(next_entities)

    def get_next_entities_recursive(self, requested_entities: List[EntityType] = None,
                                    include_current_entities: bool = False) -> NavigableEntitySet:
        """Return all the entities that are linked to the current entities

        :param requested_entities: [description]
        :type requested_entities: List[EntityType]
        :return: [description]
        :rtype: NavigableEntitySet
        """
        if self.is_empty():
            return NavigableEntitySet()

        if requested_entities is None:
            requested_entities = self._all_entity_types

        loaded_entities = NavigableEntitySet(self._entities, 0)
        self._get_next_entities_recursive(requested_entities, loaded_entities, 1)

        if not include_current_entities:
            loaded_entities.remove_deep(0)

        return loaded_entities

    def _get_next_entities_recursive(
            self, requested_entities: List[EntityType],
            loaded_entities: NavigableEntitySet,
            deep_level: int) -> NavigableEntitySet:

        if self.is_empty():
            return loaded_entities

        if EntityType.EXPERIMENT in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities, loaded_entities, self.get_next_experiments(),
                EntityNavigatorExperiment, deep_level)

        if EntityType.RESOURCE in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities, loaded_entities, self.get_next_resources(),
                EntityNavigatorResource, deep_level)

        if EntityType.REPORT in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities, loaded_entities, self.get_next_reports(),
                EntityNavigatorReport, deep_level)

        if EntityType.VIEW in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities, loaded_entities, self.get_next_views(),
                EntityNavigatorView, deep_level)

        return loaded_entities

    def _get_next_entities_type_recursive(
            self, requested_entities: List[EntityType],
            loaded_entities: NavigableEntitySet,
            entity_nav: 'EntityNavigator',
            nav_class: Type['EntityNavigator'],
            deep_level: int) -> NavigableEntitySet:

        new_entities: Set[NavigableEntity] = entity_nav.get_entities_as_set() - loaded_entities.get_entities()

        if len(new_entities) > 0:
            loaded_entities.update(new_entities, deep_level)

            next_entity_nav: EntityNavigator = nav_class(new_entities)
            next_entity_nav._get_next_entities_recursive(requested_entities, loaded_entities, deep_level + 1)

        return loaded_entities

    def get_previous_entities_recursive(self, requested_entities: List[EntityType] = None,
                                        include_current_entities: bool = False) -> NavigableEntitySet:
        """Return all the entities that are linked to the current entities

        :param requested_entities: [description]
        :type requested_entities: List[EntityType]
        :return: [description]
        :rtype: List[NavigableEntity]
        """
        if self.is_empty():
            return NavigableEntitySet()

        if requested_entities is None:
            requested_entities = self._all_entity_types

        loaded_entities = NavigableEntitySet(self._entities, 0)
        self._get_previous_entities_recursive(requested_entities, loaded_entities, 1)

        if not include_current_entities:
            loaded_entities.remove_deep(0)

        return loaded_entities

    def _get_previous_entities_recursive(
            self, requested_entities: List[EntityType],
            loaded_entities: NavigableEntitySet, deep_level: int) -> NavigableEntitySet:

        if self.is_empty():
            return loaded_entities

        if EntityType.EXPERIMENT in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities, loaded_entities, self.get_previous_experiments(),
                EntityNavigatorExperiment, deep_level)

        if EntityType.RESOURCE in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities, loaded_entities, self.get_previous_resources(),
                EntityNavigatorResource, deep_level)

        if EntityType.REPORT in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities, loaded_entities, self.get_previous_reports(),
                EntityNavigatorReport, deep_level)

        if EntityType.VIEW in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities, loaded_entities, self.get_previous_views(),
                EntityNavigatorView, deep_level)

        return loaded_entities

    def _get_previous_entities_type_recursive(
            self, requested_entities: List[EntityType],
            loaded_entities: NavigableEntitySet,
            entity_nav: 'EntityNavigator',
            nav_class: Type['EntityNavigator'],
            deep_level: int) -> NavigableEntitySet:

        new_entities: Set[NavigableEntity] = entity_nav.get_entities_as_set() - loaded_entities.get_entities()

        if len(new_entities) > 0:
            loaded_entities.update(new_entities, deep_level)

            previous_entity_nav: EntityNavigator = nav_class(new_entities)
            previous_entity_nav._get_previous_entities_recursive(requested_entities, loaded_entities, deep_level + 1)

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

    def get_as_nav_set(self) -> NavigableEntitySet:
        return NavigableEntitySet(self._entities, 0)

    def get_entities_as_set(self) -> Set[GenericNavigableEntity]:
        return self._entities

    def get_entities_list(self) -> List[GenericNavigableEntity]:
        return list(self._entities)

    def propagate_tags(self, tags: List[Tag], entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None) -> None:
        pass

    def _propagate_tags(self, tags: List[Tag], entity: GenericNavigableEntity,
                        new_origin_type: TagOriginType, new_origin_id: str,
                        entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None):

        if entity_tags_cache is None:
            entity_tags_cache = {}

        if entity not in entity_tags_cache:
            entity_tags_cache[entity] = EntityTagList.find_by_entity(entity.get_entity_type(), entity.id)

        entity_tags = entity_tags_cache[entity]

        new_tags = [tag.propagate(new_origin_type, new_origin_id) for tag in tags]
        entity_tags.add_tags(new_tags)

    def delete_propagated_tags(self, tags: List[Tag], entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None):
        pass

    def _delete_propagated_tags(self, tags: List[Tag], entity: GenericNavigableEntity,
                                origin_type: TagOriginType, origin_id: str,
                                entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None):

        if entity_tags_cache is None:
            entity_tags_cache = {}

        if entity not in entity_tags_cache:
            entity_tags_cache[entity] = EntityTagList.find_by_entity(entity.get_entity_type(), entity.id)

        entity_tags = entity_tags_cache[entity]

        new_tags = [tag.propagate(origin_type, origin_id) for tag in tags]
        entity_tags.delete_tags(new_tags)

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


class EntityNavigatorExperiment(EntityNavigator[Experiment]):

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

    def propagate_tags(self, tags: List[Tag], entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None) -> None:

        for experiment in self._entities:

            # Propagate to resources
            next_resources = self.get_next_resources()
            for resource in next_resources.get_entities_list():
                self._propagate_tags(tags=tags, entity=resource,
                                     new_origin_type=TagOriginType.EXPERIMENT_PROPAGATED, new_origin_id=experiment.id,
                                     entity_tags_cache=entity_tags_cache)
            next_resources.propagate_tags(tags, entity_tags_cache)

            # Propagate to reports
            next_reports = self.get_next_reports()
            for report in next_reports.get_entities_list():
                self._propagate_tags(tags=tags, entity=report,
                                     new_origin_type=TagOriginType.EXPERIMENT_PROPAGATED, new_origin_id=experiment.id,
                                     entity_tags_cache=entity_tags_cache)
            next_reports.propagate_tags(tags, entity_tags_cache)

    def delete_propagated_tags(self, tags: List[Tag], entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None):

        for experiment in self._entities:

            # Propagate to resources
            next_resources = self.get_next_resources()
            for resource in next_resources.get_entities_list():
                self._delete_propagated_tags(
                    tags=tags, entity=resource, origin_type=TagOriginType.EXPERIMENT_PROPAGATED,
                    origin_id=experiment.id, entity_tags_cache=entity_tags_cache)
            next_resources.delete_propagated_tags(tags, entity_tags_cache)

            # Propagate to reports
            next_reports = self.get_next_reports()
            for report in next_reports.get_entities_list():
                self._delete_propagated_tags(
                    tags=tags, entity=report, origin_type=TagOriginType.EXPERIMENT_PROPAGATED,
                    origin_id=experiment.id, entity_tags_cache=entity_tags_cache)
            next_reports.delete_propagated_tags(tags, entity_tags_cache)


class EntityNavigatorResource(EntityNavigator[ResourceModel]):

    def get_next_reports(self) -> 'EntityNavigatorReport':
        return self.get_next_views().get_next_reports()

    def get_next_views(self) -> 'EntityNavigatorView':
        views = set(ViewConfig.get_by_resources(self._get_entities_ids()))
        return EntityNavigatorView(views)

    def get_next_resources(self) -> 'EntityNavigatorResource':
        """Return all the output resources of tasks that use the resource as input

        :return: _description_
        :rtype: EntityNavigatorResource
        """
        tasks_model = self._get_next_tasks()

        task_model_ids = [task.id for task in tasks_model]

        resources = set(ResourceModel.get_by_task_models(task_model_ids))

        return EntityNavigatorResource(resources)

    def _get_next_tasks(self) -> Set[TaskModel]:
        # retrieve all the tasks that uses the resource as input
        # Don't retrieve the Source task that uses this resource as Config because the output of the Source task
        # is the resource itself
        task_input_models: Set[TaskInputModel] = set(TaskInputModel.get_by_resource_models(self._get_entities_ids()))
        return {task_input.task_model for task_input in task_input_models}

    def get_next_experiments(self) -> 'EntityNavigatorExperiment':
        """Return all the experiments that use the resource in a source task or as input of a task"""
        return EntityNavigatorExperiment(list(self.get_next_experiments_select_model()))

    def get_next_experiments_select_model(self) -> ModelSelect:
        """Return all the experiments that use the resource in a source task or as input of a task"""
        expression = (TaskInputModel.resource_model.in_(self._get_entities_ids())) | (
            TaskModel.source_config_id.in_(self._get_entities_ids()))

        resource_exp_ids = {resource.experiment.id for resource in self._entities if resource.experiment is not None}
        # Exclude the experiment that generated the resource from the select
        if len(resource_exp_ids) > 0:
            expression = expression & (Experiment.id.not_in(resource_exp_ids))

        # Search experiment where a Source is configured with the resource and where a task takes the resource as input
            # with this, all case are managed
        return Experiment.select().where(expression) \
            .join(TaskInputModel, JOIN.LEFT_OUTER) \
            .join(TaskModel, JOIN.LEFT_OUTER, on=(Experiment.id == TaskModel.experiment)) \
            .distinct()

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

        experiments: Set[Experiment] = set(Experiment.get_by_ids(experiment_ids))

        return EntityNavigatorExperiment(experiments)

    def propagate_tags(self, tags: List[Tag], entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None) -> None:

        for resource in self._entities:

            # Propagate to next views
            next_views = self.get_next_views()
            for view in next_views.get_entities_list():
                self._propagate_tags(tags=tags, entity=view,
                                     new_origin_type=TagOriginType.RESOURCE_PROPAGATED, new_origin_id=resource.id,
                                     entity_tags_cache=entity_tags_cache)
            next_views.propagate_tags(tags, entity_tags_cache)

            # Propagate to next resources
            next_resources = self.get_next_resources()
            for next_resource in next_resources.get_entities_list():
                if next_resource.task_model:
                    self._propagate_tags(
                        tags=tags, entity=next_resource,
                        new_origin_type=TagOriginType.TASK_PROPAGATED, new_origin_id=resource.task_model.id,
                        entity_tags_cache=entity_tags_cache)
            next_resources.propagate_tags(tags, entity_tags_cache)

    def delete_propagated_tags(self, tags: List[Tag], entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None):

        for resource in self._entities:

            # Propagate to next views
            next_views = self.get_next_views()
            for view in next_views.get_entities_list():
                self._delete_propagated_tags(
                    tags=tags, entity=view, origin_type=TagOriginType.RESOURCE_PROPAGATED,
                    origin_id=resource.id, entity_tags_cache=entity_tags_cache)
            next_views.delete_propagated_tags(tags, entity_tags_cache)

            # Propagate to next resources
            next_resources = self.get_next_resources()
            for next_resource in next_resources.get_entities_list():
                if next_resource.task_model:
                    self._delete_propagated_tags(
                        tags=tags, entity=next_resource, origin_type=TagOriginType.TASK_PROPAGATED,
                        origin_id=resource.task_model.id, entity_tags_cache=entity_tags_cache)
            next_resources.delete_propagated_tags(tags, entity_tags_cache)


class EntityNavigatorView(EntityNavigator[ViewConfig]):

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

    def propagate_tags(self, tags: List[Tag], entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None) -> None:

        for view in self._entities:
            # Propagate to next reports
            next_reports = self.get_next_reports()
            for report in next_reports.get_entities_list():
                self._propagate_tags(tags=tags, entity=report,
                                     new_origin_type=TagOriginType.VIEW_PROPAGATED, new_origin_id=view.id,
                                     entity_tags_cache=entity_tags_cache)
            next_reports.propagate_tags(tags, entity_tags_cache)

    def delete_propagated_tags(self, tags: List[Tag], entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None):

        for view in self._entities:
            # Propagate to next reports
            next_reports = self.get_next_reports()
            for report in next_reports.get_entities_list():
                self._delete_propagated_tags(
                    tags=tags, entity=report, origin_type=TagOriginType.VIEW_PROPAGATED,
                    origin_id=view.id, entity_tags_cache=entity_tags_cache)
            next_reports.delete_propagated_tags(tags, entity_tags_cache)


class EntityNavigatorReport(EntityNavigator[Report]):

    def get_previous_views(self) -> 'EntityNavigatorView':
        report_views: List[ReportViewModel] = list(ReportViewModel.get_by_reports(self._get_entities_ids()))

        return EntityNavigatorView({report_view.view for report_view in report_views})

    def get_previous_resources(self) -> 'EntityNavigatorResource':
        return self.get_previous_views().get_previous_resources()

    def get_previous_experiments(self) -> 'EntityNavigatorExperiment':
        return self.get_previous_resources().get_previous_experiments()
