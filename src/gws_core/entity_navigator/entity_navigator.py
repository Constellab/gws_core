

from typing import (Dict, Generic, Iterable, List, Optional, Set, Type,
                    TypeVar, Union)

from peewee import JOIN, ModelSelect

from gws_core.entity_navigator.entity_navigator_deep import NavigableEntitySet
from gws_core.entity_navigator.entity_navigator_type import (
    NavigableEntity, NavigableEntityType)
from gws_core.note.note import Note, NoteScenario
from gws_core.note.note_view_model import NoteViewModel
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.scenario.scenario import Scenario
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag
from gws_core.tag.tag_dto import TagOriginType
from gws_core.task.task_input_model import TaskInputModel
from gws_core.task.task_model import TaskModel

GenericNavigableEntity = TypeVar('GenericNavigableEntity', bound=NavigableEntity)


class EntityNavigator(Generic[GenericNavigableEntity]):

    _entities: Set[GenericNavigableEntity]

    _all_entity_types = [NavigableEntityType.SCENARIO, NavigableEntityType.RESOURCE,
                         NavigableEntityType.VIEW, NavigableEntityType.NOTE]

    def __init__(self, entities: Union[GenericNavigableEntity, Iterable[GenericNavigableEntity]]):
        if entities is None:
            self._entities = set()
        elif isinstance(entities, Iterable):
            self._entities = set(entities)
        else:
            self._entities = set([entities])

    def has_next_entities(self, requested_entities: List[NavigableEntityType] = None) -> bool:
        if requested_entities is None:
            requested_entities = self._all_entity_types
        return len(self.get_next_entities(requested_entities)) > 0

    def get_next_entities(self, requested_entities: List[NavigableEntityType]) -> NavigableEntitySet:
        """Return all the entities that are linked to the current entities

        :param requested_entities: [description]
        :type requested_entities: List[EntityType]
        :return: [description]
        :rtype: NavigableEntitySet
        """
        if self.is_empty():
            return NavigableEntitySet()

        next_entities = set()

        if NavigableEntityType.SCENARIO in requested_entities:
            next_entities.update(self.get_next_scenarios().get_entities_as_set())

        if NavigableEntityType.RESOURCE in requested_entities:
            next_entities.update(self.get_next_resources().get_entities_as_set())

        if NavigableEntityType.NOTE in requested_entities:
            next_entities.update(self.get_next_notes().get_entities_as_set())

        if NavigableEntityType.VIEW in requested_entities:
            next_entities.update(self.get_next_views().get_entities_as_set())

        return NavigableEntitySet(next_entities)

    def get_next_entities_recursive(self, requested_entities: List[NavigableEntityType] = None,
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
            self, requested_entities: List[NavigableEntityType],
            loaded_entities: NavigableEntitySet,
            deep_level: int) -> NavigableEntitySet:

        if self.is_empty():
            return loaded_entities

        if NavigableEntityType.SCENARIO in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities, loaded_entities, self.get_next_scenarios(),
                EntityNavigatorScenario, deep_level)

        if NavigableEntityType.RESOURCE in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities, loaded_entities, self.get_next_resources(),
                EntityNavigatorResource, deep_level)

        if NavigableEntityType.NOTE in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities, loaded_entities, self.get_next_notes(),
                EntityNavigatorNote, deep_level)

        if NavigableEntityType.VIEW in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities, loaded_entities, self.get_next_views(),
                EntityNavigatorView, deep_level)

        return loaded_entities

    def _get_next_entities_type_recursive(
            self, requested_entities: List[NavigableEntityType],
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

    def get_previous_entities_recursive(self, requested_entities: List[NavigableEntityType] = None,
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
            self, requested_entities: List[NavigableEntityType],
            loaded_entities: NavigableEntitySet, deep_level: int) -> NavigableEntitySet:

        if self.is_empty():
            return loaded_entities

        if NavigableEntityType.SCENARIO in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities, loaded_entities, self.get_previous_scenarios(),
                EntityNavigatorScenario, deep_level)

        if NavigableEntityType.RESOURCE in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities, loaded_entities, self.get_previous_resources(),
                EntityNavigatorResource, deep_level)

        if NavigableEntityType.NOTE in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities, loaded_entities, self.get_previous_notes(),
                EntityNavigatorNote, deep_level)

        if NavigableEntityType.VIEW in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities, loaded_entities, self.get_previous_views(),
                EntityNavigatorView, deep_level)

        return loaded_entities

    def _get_previous_entities_type_recursive(
            self, requested_entities: List[NavigableEntityType],
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

    def get_next_notes(self) -> 'EntityNavigatorNote':
        return EntityNavigatorNote(set())

    def get_next_views(self) -> 'EntityNavigatorView':
        return EntityNavigatorView(set())

    def get_next_resources(self) -> 'EntityNavigatorResource':
        return EntityNavigatorResource(set())

    def get_next_scenarios(self) -> 'EntityNavigatorScenario':
        return EntityNavigatorScenario(set())

    def get_previous_notes(self) -> 'EntityNavigatorNote':
        return EntityNavigatorNote(set())

    def get_previous_views(self) -> 'EntityNavigatorView':
        return EntityNavigatorView(set())

    def get_previous_resources(self) -> 'EntityNavigatorResource':
        return EntityNavigatorResource(set())

    def get_previous_scenarios(self) -> 'EntityNavigatorScenario':
        return EntityNavigatorScenario(set())

    def get_as_nav_set(self) -> NavigableEntitySet:
        return NavigableEntitySet(self._entities, 0)

    def get_entities_as_set(self) -> Set[GenericNavigableEntity]:
        return self._entities

    def get_entities_list(self) -> List[GenericNavigableEntity]:
        return list(self._entities)

    def has_entities(self) -> bool:
        return len(self._entities) > 0

    def get_first_entity(self) -> Optional[GenericNavigableEntity]:
        entities = self.get_entities_list()
        return entities[0] if len(entities) > 0 else None

    def propagate_tags(self, tags: List[Tag], entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None) -> None:
        pass

    def _propagate_tags(self, tags: List[Tag], entity: GenericNavigableEntity,
                        new_origin_type: TagOriginType, new_origin_id: str,
                        entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None):

        if entity_tags_cache is None:
            entity_tags_cache = {}

        if entity not in entity_tags_cache:
            entity_tags_cache[entity] = EntityTagList.find_by_entity(entity.get_navigable_entity_type(), entity.id)

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
            entity_tags_cache[entity] = EntityTagList.find_by_entity(entity.get_navigable_entity_type(), entity.id)

        entity_tags = entity_tags_cache[entity]

        new_tags = [tag.propagate(origin_type, origin_id) for tag in tags]
        entity_tags.delete_tags(new_tags)

    def is_empty(self) -> bool:
        return len(self._entities) == 0

    def _get_entities_ids(self) -> List[str]:
        return [entity.id for entity in self._entities]

    # TODO A VOIR
    @classmethod
    def from_entity_id(cls, entity_type: NavigableEntityType, entity_id: str) -> 'EntityNavigator':
        if entity_type == NavigableEntityType.SCENARIO:
            return EntityNavigatorScenario(Scenario.get_by_id_and_check(entity_id))
        elif entity_type == NavigableEntityType.NOTE:
            return EntityNavigatorView(Note.get_by_id_and_check(entity_id))
        elif entity_type == NavigableEntityType.VIEW:
            return EntityNavigatorNote(ViewConfig.get_by_id_and_check(entity_id))
        elif entity_type == NavigableEntityType.RESOURCE:
            return EntityNavigatorResource(ResourceModel.get_by_id_and_check(entity_id))

        raise Exception(f"Entity type {entity_type} not supported")


class EntityNavigatorScenario(EntityNavigator[Scenario]):

    def get_next_notes(self) -> 'EntityNavigatorNote':
        notes = set(NoteScenario.find_notes_by_scenarios(self._get_entities_ids()))
        return EntityNavigatorNote(notes)

    def get_next_views(self) -> 'EntityNavigatorView':
        return self.get_next_resources().get_next_views()

    def get_next_resources(self) -> 'EntityNavigatorResource':
        """Return all the resources generated by the scenarios"""
        resources = set(ResourceModel.get_by_scenarios(self._get_entities_ids()))
        return EntityNavigatorResource(resources)

    def get_next_scenarios(self) -> 'EntityNavigatorScenario':
        return self.get_next_resources().get_next_scenarios()

    def get_previous_resources(self) -> 'EntityNavigatorResource':
        task_models: List[TaskModel] = list(TaskModel.get_scenario_input_tasks(self._get_entities_ids()))

        resource_ids: List[str] = [task.source_config_id for task in task_models if task.source_config_id is not None]

        return EntityNavigatorResource(ResourceModel.get_by_ids(resource_ids))

    def get_previous_scenarios(self) -> 'EntityNavigatorScenario':
        return self.get_previous_resources().get_previous_scenarios()

    def propagate_tags(self, tags: List[Tag], entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None) -> None:

        for scenario in self._entities:

            # Propagate to resources
            next_resources = self.get_next_resources()
            for resource in next_resources.get_entities_list():
                self._propagate_tags(tags=tags, entity=resource,
                                     new_origin_type=TagOriginType.SCENARIO_PROPAGATED, new_origin_id=scenario.id,
                                     entity_tags_cache=entity_tags_cache)
            next_resources.propagate_tags(tags, entity_tags_cache)

            # Propagate to notes
            next_notes = self.get_next_notes()
            for note in next_notes.get_entities_list():
                self._propagate_tags(tags=tags, entity=note,
                                     new_origin_type=TagOriginType.SCENARIO_PROPAGATED, new_origin_id=scenario.id,
                                     entity_tags_cache=entity_tags_cache)
            next_notes.propagate_tags(tags, entity_tags_cache)

    def delete_propagated_tags(self, tags: List[Tag], entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None):

        for scenario in self._entities:

            # Propagate to resources
            next_resources = self.get_next_resources()
            for resource in next_resources.get_entities_list():
                self._delete_propagated_tags(
                    tags=tags, entity=resource, origin_type=TagOriginType.SCENARIO_PROPAGATED,
                    origin_id=scenario.id, entity_tags_cache=entity_tags_cache)
            next_resources.delete_propagated_tags(tags, entity_tags_cache)

            # Propagate to notes
            next_notes = self.get_next_notes()
            for note in next_notes.get_entities_list():
                self._delete_propagated_tags(
                    tags=tags, entity=note, origin_type=TagOriginType.SCENARIO_PROPAGATED,
                    origin_id=scenario.id, entity_tags_cache=entity_tags_cache)
            next_notes.delete_propagated_tags(tags, entity_tags_cache)


class EntityNavigatorResource(EntityNavigator[ResourceModel]):

    def get_next_notes(self) -> 'EntityNavigatorNote':
        return self.get_next_views().get_next_notes()

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
        # Don't retrieve the input task that uses this resource as Config because the output of the input task
        # is the resource itself
        task_input_models: Set[TaskInputModel] = set(TaskInputModel.get_by_resource_models(self._get_entities_ids()))
        return {task_input.task_model for task_input in task_input_models}

    def get_next_scenarios(self) -> 'EntityNavigatorScenario':
        """Return all the scenarios that use the resource in a source task or as input of a task"""
        return EntityNavigatorScenario(list(self.get_next_scenarios_select_model()))

    def get_next_scenarios_select_model(self) -> ModelSelect:
        """Return all the scenarios that use the resource in a source task or as input of a task"""
        expression = (TaskInputModel.resource_model.in_(self._get_entities_ids())) | (
            TaskModel.source_config_id.in_(self._get_entities_ids()))

        resource_exp_ids = {resource.scenario.id for resource in self._entities if resource.scenario is not None}
        # Exclude the scenario that generated the resource from the select
        if len(resource_exp_ids) > 0:
            expression = expression & (Scenario.id.not_in(resource_exp_ids))

        # Search scenario where an input task is configured with the resource and where a task takes the resource as input
            # with this, all case are managed
        return Scenario.select().where(expression) \
            .join(TaskInputModel, JOIN.LEFT_OUTER) \
            .join(TaskModel, JOIN.LEFT_OUTER, on=(Scenario.id == TaskModel.scenario)) \
            .distinct()

    def get_previous_resources(self) -> 'EntityNavigatorResource':
        # retrieve the tasks that generated the current resources
        task_model_ids = [resource.task_model.id for resource in self._entities if resource.task_model is not None]

        # retrieve all the inputs of the tasks
        task_input_model: List[TaskInputModel] = list(TaskInputModel.get_by_task_models(task_model_ids))

        resources = {task_input.resource_model for task_input in task_input_model}

        return EntityNavigatorResource(resources)

    def get_previous_scenarios(self) -> 'EntityNavigatorScenario':
        """ Return all the scenarios that generated the current resources"""

        scenario_ids: List[str] = [resource.scenario.id for resource in self._entities
                                   if resource.scenario is not None]

        scenarios: Set[Scenario] = set(Scenario.get_by_ids(scenario_ids))

        return EntityNavigatorScenario(scenarios)

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
                        new_origin_type=TagOriginType.TASK_PROPAGATED, new_origin_id=next_resource.task_model.id,
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

    def get_next_notes(self) -> 'EntityNavigatorNote':

        note_views: List[NoteViewModel] = list(NoteViewModel.get_by_views(self._get_entities_ids()))

        notes = set([note_view.note for note_view in note_views])

        return EntityNavigatorNote(notes)

    def get_previous_resources(self) -> 'EntityNavigatorResource':
        resource_ids: List[str] = [view.resource_model.id for view in self._entities if view.resource_model is not None]

        resources = set(ResourceModel.get_by_ids(resource_ids))

        return EntityNavigatorResource(resources)

    def get_previous_scenarios(self) -> 'EntityNavigatorScenario':
        return self.get_previous_resources().get_previous_scenarios()

    def _get_resources(self) -> List[ResourceModel]:
        return [view.resource_model for view in self._entities]

    def propagate_tags(self, tags: List[Tag], entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None) -> None:

        for view in self._entities:
            # Propagate to next notes
            next_notes = self.get_next_notes()
            for note in next_notes.get_entities_list():
                self._propagate_tags(tags=tags, entity=note,
                                     new_origin_type=TagOriginType.VIEW_PROPAGATED, new_origin_id=view.id,
                                     entity_tags_cache=entity_tags_cache)
            next_notes.propagate_tags(tags, entity_tags_cache)

    def delete_propagated_tags(self, tags: List[Tag], entity_tags_cache: Dict[NavigableEntity, EntityTagList] = None):

        for view in self._entities:
            # Propagate to next notes
            next_notes = self.get_next_notes()
            for note in next_notes.get_entities_list():
                self._delete_propagated_tags(
                    tags=tags, entity=note, origin_type=TagOriginType.VIEW_PROPAGATED,
                    origin_id=view.id, entity_tags_cache=entity_tags_cache)
            next_notes.delete_propagated_tags(tags, entity_tags_cache)


class EntityNavigatorNote(EntityNavigator[Note]):

    def get_previous_views(self) -> 'EntityNavigatorView':
        note_views: List[NoteViewModel] = list(NoteViewModel.get_by_notes(self._get_entities_ids()))

        return EntityNavigatorView({note_view.view for note_view in note_views})

    def get_previous_resources(self) -> 'EntityNavigatorResource':
        return self.get_previous_views().get_previous_resources()

    def get_previous_scenarios(self) -> 'EntityNavigatorScenario':
        return self.get_previous_resources().get_previous_scenarios()
