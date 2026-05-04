from collections.abc import Iterable
from typing import Generic, TypeVar

from peewee import JOIN, ModelSelect

from gws_core.entity_navigator.entity_navigator_deep import NavigableEntitySet
from gws_core.entity_navigator.entity_navigator_type import NavigableEntity, NavigableEntityType
from gws_core.form.form import Form
from gws_core.form_template.form_template import FormTemplate
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

GenericNavigableEntity = TypeVar("GenericNavigableEntity", bound=NavigableEntity)


class EntityNavigator(Generic[GenericNavigableEntity]):
    """Navigate the lineage graph of scenarios, resources, views and notes.

    A navigator wraps a set of entities of one type and exposes traversals to
    their direct and transitive neighbors (next/previous), plus tag propagation
    over the same graph.

    Two traversal flavors coexist and are intentionally separate:

    - ``get_next_entities_recursive`` / ``get_previous_entities_recursive`` collect
      every reachable entity into a flat ``NavigableEntitySet`` (with depth info)
      and discard edge information. Use these for "what's impacted" queries.
    - ``propagate_tags`` / ``delete_propagated_tags`` walk the same graph but must
      preserve per-edge provenance: each propagated tag carries an origin
      (``TagOrigin``) describing the immediate upstream entity that caused it.
      Because the origin depends on the edge kind (e.g. resource->view vs.
      resource->resource), these methods cannot be expressed on top of the
      flat-set recursion without losing attribution.

    Both flavors apply the same two performance rules: hoist
    ``get_next_*()``/``get_previous_*()`` queries out of per-entity loops, and
    skip already-visited entities so reconverging paths don't re-walk subgraphs.
    """

    _entities: set[GenericNavigableEntity]

    _all_entity_types = [
        NavigableEntityType.SCENARIO,
        NavigableEntityType.RESOURCE,
        NavigableEntityType.VIEW,
        NavigableEntityType.NOTE,
    ]

    def __init__(self, entities: GenericNavigableEntity | Iterable[GenericNavigableEntity]):
        if entities is None:
            self._entities = set()
        elif isinstance(entities, Iterable):
            self._entities = set(entities)
        else:
            self._entities = {entities}

    def has_next_entities(
        self, requested_entities: list[NavigableEntityType] | None = None
    ) -> bool:
        """Return True if any direct downstream neighbor exists.

        :param requested_entities: entity types to consider as neighbors.
            Defaults to all four navigable types.
        """
        if requested_entities is None:
            requested_entities = self._all_entity_types
        return len(self.get_next_entities(requested_entities)) > 0

    def get_next_entities(
        self, requested_entities: list[NavigableEntityType]
    ) -> NavigableEntitySet:
        """Return the direct downstream neighbors of the wrapped entities.

        Only one hop is followed (no recursion). Entities of any type listed in
        ``requested_entities`` are merged into a single ``NavigableEntitySet``.
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

    def get_next_entities_recursive(
        self,
        requested_entities: list[NavigableEntityType] | None = None,
        include_current_entities: bool = False,
    ) -> NavigableEntitySet:
        """Return every entity transitively reachable downstream.

        Traverses the lineage graph breadth-first. Each entity is visited once,
        annotated with its depth in the returned ``NavigableEntitySet``. Use this
        for impact analysis ("what entities would be affected"). Edge-level
        provenance is not preserved -- if you need to know which immediate
        upstream caused a given downstream to be reached, use ``propagate_tags``
        instead.

        :param requested_entities: entity types to consider during traversal.
            Defaults to all four navigable types.
        :param include_current_entities: if True, the wrapped entities are kept
            in the result at depth 0; otherwise only their descendants are
            returned.
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
        self,
        requested_entities: list[NavigableEntityType],
        loaded_entities: NavigableEntitySet,
        deep_level: int,
    ) -> NavigableEntitySet:
        if self.is_empty():
            return loaded_entities

        if NavigableEntityType.SCENARIO in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities,
                loaded_entities,
                self.get_next_scenarios(),
                EntityNavigatorScenario,
                deep_level,
            )

        if NavigableEntityType.RESOURCE in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities,
                loaded_entities,
                self.get_next_resources(),
                EntityNavigatorResource,
                deep_level,
            )

        if NavigableEntityType.NOTE in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities,
                loaded_entities,
                self.get_next_notes(),
                EntityNavigatorNote,
                deep_level,
            )

        if NavigableEntityType.VIEW in requested_entities:
            self._get_next_entities_type_recursive(
                requested_entities,
                loaded_entities,
                self.get_next_views(),
                EntityNavigatorView,
                deep_level,
            )

        return loaded_entities

    def _get_next_entities_type_recursive(
        self,
        requested_entities: list[NavigableEntityType],
        loaded_entities: NavigableEntitySet,
        entity_nav: "EntityNavigator",
        nav_class: type["EntityNavigator"],
        deep_level: int,
    ) -> NavigableEntitySet:
        all_next_entities = entity_nav.get_entities_as_set()
        already_loaded_entities = all_next_entities & loaded_entities.get_entities()
        new_entities = all_next_entities - already_loaded_entities

        # Update deep_level for already loaded entities found at a deeper level.
        # This ensures correct deletion ordering when an entity is reachable
        # from multiple paths at different depths.
        for entity in already_loaded_entities:
            loaded_entities.add(entity, deep_level)

        if len(new_entities) > 0:
            loaded_entities.update(new_entities, deep_level)

            next_entity_nav: EntityNavigator = nav_class(new_entities)
            next_entity_nav._get_next_entities_recursive(
                requested_entities, loaded_entities, deep_level + 1
            )

        return loaded_entities

    def get_previous_entities_recursive(
        self,
        requested_entities: list[NavigableEntityType] | None = None,
        include_current_entities: bool = False,
    ) -> NavigableEntitySet:
        """Return every entity transitively reachable upstream.

        Mirror of ``get_next_entities_recursive`` but walks the lineage graph in
        the opposite direction (towards ancestors).

        :param requested_entities: entity types to consider during traversal.
            Defaults to all four navigable types.
        :param include_current_entities: if True, the wrapped entities are kept
            in the result at depth 0; otherwise only their ancestors are
            returned.
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
        self,
        requested_entities: list[NavigableEntityType],
        loaded_entities: NavigableEntitySet,
        deep_level: int,
    ) -> NavigableEntitySet:
        if self.is_empty():
            return loaded_entities

        if NavigableEntityType.SCENARIO in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities,
                loaded_entities,
                self.get_previous_scenarios(),
                EntityNavigatorScenario,
                deep_level,
            )

        if NavigableEntityType.RESOURCE in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities,
                loaded_entities,
                self.get_previous_resources(),
                EntityNavigatorResource,
                deep_level,
            )

        if NavigableEntityType.NOTE in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities,
                loaded_entities,
                self.get_previous_notes(),
                EntityNavigatorNote,
                deep_level,
            )

        if NavigableEntityType.VIEW in requested_entities:
            self._get_previous_entities_type_recursive(
                requested_entities,
                loaded_entities,
                self.get_previous_views(),
                EntityNavigatorView,
                deep_level,
            )

        return loaded_entities

    def _get_previous_entities_type_recursive(
        self,
        requested_entities: list[NavigableEntityType],
        loaded_entities: NavigableEntitySet,
        entity_nav: "EntityNavigator",
        nav_class: type["EntityNavigator"],
        deep_level: int,
    ) -> NavigableEntitySet:
        all_prev_entities = entity_nav.get_entities_as_set()
        already_loaded_entities = all_prev_entities & loaded_entities.get_entities()
        new_entities = all_prev_entities - already_loaded_entities

        # Update deep_level for already loaded entities found at a deeper level
        for entity in already_loaded_entities:
            loaded_entities.add(entity, deep_level)

        if len(new_entities) > 0:
            loaded_entities.update(new_entities, deep_level)

            previous_entity_nav: EntityNavigator = nav_class(new_entities)
            previous_entity_nav._get_previous_entities_recursive(
                requested_entities, loaded_entities, deep_level + 1
            )

        return loaded_entities

    def get_next_notes(self) -> "EntityNavigatorNote":
        """Return the direct downstream notes. Empty by default; overridden by subclasses
        whose entity type has a notes-edge in the lineage graph."""
        return EntityNavigatorNote(set())

    def get_next_views(self) -> "EntityNavigatorView":
        """Return the direct downstream views. Empty by default; overridden by subclasses."""
        return EntityNavigatorView(set())

    def get_next_resources(self) -> "EntityNavigatorResource":
        """Return the direct downstream resources. Empty by default; overridden by subclasses."""
        return EntityNavigatorResource(set())

    def get_next_scenarios(self) -> "EntityNavigatorScenario":
        """Return the direct downstream scenarios. Empty by default; overridden by subclasses."""
        return EntityNavigatorScenario(set())

    def get_previous_notes(self) -> "EntityNavigatorNote":
        """Return the direct upstream notes. Empty by default; overridden by subclasses."""
        return EntityNavigatorNote(set())

    def get_previous_views(self) -> "EntityNavigatorView":
        """Return the direct upstream views. Empty by default; overridden by subclasses."""
        return EntityNavigatorView(set())

    def get_previous_resources(self) -> "EntityNavigatorResource":
        """Return the direct upstream resources. Empty by default; overridden by subclasses."""
        return EntityNavigatorResource(set())

    def get_previous_scenarios(self) -> "EntityNavigatorScenario":
        """Return the direct upstream scenarios. Empty by default; overridden by subclasses."""
        return EntityNavigatorScenario(set())

    def get_as_nav_set(self) -> NavigableEntitySet:
        """Wrap the current entities as a depth-0 ``NavigableEntitySet``."""
        return NavigableEntitySet(self._entities, 0)

    def get_entities_as_set(self) -> set[GenericNavigableEntity]:
        """Return the wrapped entities as a set."""
        return self._entities

    def get_entities_list(self) -> list[GenericNavigableEntity]:
        """Return the wrapped entities as a list. Order is not guaranteed (the
        underlying storage is a set)."""
        return list(self._entities)

    def has_entities(self) -> bool:
        """Return True if at least one entity is wrapped."""
        return len(self._entities) > 0

    def get_first_entity(self) -> GenericNavigableEntity | None:
        """Return an arbitrary entity from the set, or ``None`` if empty.

        Useful when the caller knows the navigator wraps a single entity.
        """
        entities = self.get_entities_list()
        return entities[0] if len(entities) > 0 else None

    def propagate_tags(
        self,
        tags: list[Tag],
        entity_tags_cache: dict[NavigableEntity, EntityTagList] | None = None,
        visited: set[NavigableEntity] | None = None,
    ) -> None:
        """Propagate the given tags to every transitively reachable downstream entity.

        Each propagated tag carries an origin (``TagOrigin``) describing the
        immediate upstream entity that caused it -- this is why we cannot reuse
        ``get_next_entities_recursive`` here: that method flattens the graph
        and discards edge information, while propagation needs per-edge
        attribution. The origin's type and id depend on the edge kind:
        scenario->resource yields ``SCENARIO_PROPAGATED``, resource->next-resource
        yields ``TASK_PROPAGATED``, resource->view yields ``RESOURCE_PROPAGATED``,
        view->note yields ``VIEW_PROPAGATED``.

        Performance: ``get_next_*()`` queries are hoisted out of the per-entity
        loop, and ``visited`` tracks entities whose downstream has already been
        walked so reconverging paths in the DAG don't re-walk subgraphs.

        :param tags: tags to propagate. Their origin is set per edge during the walk.
        :param entity_tags_cache: shared cache mapping entity to its tag list,
            populated as the walk progresses. Pass ``None`` for top-level calls;
            recursive calls thread the same cache through.
        :param visited: shared set of entities whose downstream has already been
            walked. Pass ``None`` for top-level calls; recursive calls thread the
            same set through. Distinct from ``entity_tags_cache`` because an
            entity being tagged by a parent is not the same as that entity's own
            downstream having been traversed.
        """
        pass

    def _propagate_tags(
        self,
        tags: list[Tag],
        entity: NavigableEntity,
        new_origin_type: TagOriginType,
        new_origin_id: str,
        entity_tags_cache: dict[NavigableEntity, EntityTagList] | None = None,
    ):
        """Add ``tags`` to a single ``entity`` with the given origin, using the cache.

        ``entity`` is typed as ``NavigableEntity`` (not the navigator's own
        ``GenericNavigableEntity``) because propagation crosses entity types --
        e.g. an ``EntityNavigatorScenario`` writes tags onto downstream resources
        and notes, not just scenarios.
        """
        if entity_tags_cache is None:
            entity_tags_cache = {}

        if entity not in entity_tags_cache:
            tag_type = entity.get_navigable_entity_type().convert_to_tag_entity_type()
            entity_tags_cache[entity] = EntityTagList.find_by_entity(tag_type, entity.id)

        entity_tags = entity_tags_cache[entity]

        new_tags = [tag.propagate(new_origin_type, new_origin_id) for tag in tags]
        entity_tags.add_tags(new_tags)

    def delete_propagated_tags(
        self,
        tags: list[Tag],
        entity_tags_cache: dict[NavigableEntity, EntityTagList] | None = None,
        visited: set[NavigableEntity] | None = None,
    ):
        """Remove previously propagated copies of ``tags`` from every reachable downstream entity.

        Inverse of ``propagate_tags`` -- traverses the same graph with the same
        per-edge origin attribution and deletes the matching tag entries.
        See ``propagate_tags`` for why this cannot be expressed on top of
        ``get_next_entities_recursive``.

        :param tags: tags whose propagated copies should be removed.
        :param entity_tags_cache: shared cache mapping entity to its tag list,
            populated as the walk progresses.
        :param visited: shared set of entities whose downstream has already been
            walked.
        """
        pass

    def _delete_propagated_tags(
        self,
        tags: list[Tag],
        entity: NavigableEntity,
        origin_type: TagOriginType,
        origin_id: str,
        entity_tags_cache: dict[NavigableEntity, EntityTagList] | None = None,
    ):
        """Remove a propagated copy of ``tags`` from a single ``entity``, populating the cache.

        ``entity`` is typed as ``NavigableEntity`` for the same reason as
        ``_propagate_tags``: deletion crosses entity types.
        """
        if entity_tags_cache is None:
            entity_tags_cache = {}

        if entity not in entity_tags_cache:
            tag_type = entity.get_navigable_entity_type().convert_to_tag_entity_type()
            entity_tags_cache[entity] = EntityTagList.find_by_entity(tag_type, entity.id)

        entity_tags = entity_tags_cache[entity]

        new_tags = [tag.propagate(origin_type, origin_id) for tag in tags]
        entity_tags.delete_tags(new_tags)

    def is_empty(self) -> bool:
        """Return True if no entities are wrapped."""
        return len(self._entities) == 0

    def _get_entities_ids(self) -> list[str]:
        return [entity.id for entity in self._entities]

    @classmethod
    def from_entity_id(cls, entity_type: NavigableEntityType, entity_id: str) -> "EntityNavigator":
        """Build the appropriate concrete navigator for a single entity, by type and id.

        Raises if the entity does not exist or if ``entity_type`` is unknown.
        """
        if entity_type == NavigableEntityType.SCENARIO:
            return EntityNavigatorScenario(Scenario.get_by_id_and_check(entity_id))
        elif entity_type == NavigableEntityType.NOTE:
            return EntityNavigatorNote(Note.get_by_id_and_check(entity_id))
        elif entity_type == NavigableEntityType.VIEW:
            return EntityNavigatorView(ViewConfig.get_by_id_and_check(entity_id))
        elif entity_type == NavigableEntityType.RESOURCE:
            return EntityNavigatorResource(ResourceModel.get_by_id_and_check(entity_id))
        elif entity_type == NavigableEntityType.FORM_TEMPLATE:
            return EntityNavigatorFormTemplate(FormTemplate.get_by_id_and_check(entity_id))
        elif entity_type == NavigableEntityType.FORM:
            return EntityNavigatorForm(Form.get_by_id_and_check(entity_id))

        raise Exception(f"Entity type {entity_type} not supported")


class EntityNavigatorScenario(EntityNavigator[Scenario]):
    """Navigator over scenarios. Edges: scenario -> resources it produces and notes attached to it."""

    def get_next_notes(self) -> "EntityNavigatorNote":
        """Return notes attached to the wrapped scenarios via ``NoteScenario``."""
        notes = set(NoteScenario.find_notes_by_scenarios(self._get_entities_ids()))
        return EntityNavigatorNote(notes)

    def get_next_views(self) -> "EntityNavigatorView":
        """Return views of the resources produced by the wrapped scenarios."""
        return self.get_next_resources().get_next_views()

    def get_next_resources(self) -> "EntityNavigatorResource":
        """Return all the resources generated by the wrapped scenarios."""
        resources = set(ResourceModel.get_by_scenarios(self._get_entities_ids()))
        return EntityNavigatorResource(resources)

    def get_next_scenarios(self) -> "EntityNavigatorScenario":
        """Return scenarios that consume any resource produced by the wrapped scenarios."""
        return self.get_next_resources().get_next_scenarios()

    def get_previous_resources(self) -> "EntityNavigatorResource":
        """Return resources consumed by the wrapped scenarios via input tasks.

        Walks ``TaskModel.source_config_id`` of the scenarios' input tasks.
        """
        task_models: list[TaskModel] = list(
            TaskModel.get_scenario_input_tasks(self._get_entities_ids())
        )

        resource_ids: list[str] = [
            task.source_config_id for task in task_models if task.source_config_id is not None
        ]

        return EntityNavigatorResource(ResourceModel.get_by_ids(resource_ids))

    def get_previous_scenarios(self) -> "EntityNavigatorScenario":
        """Return scenarios that produced any resource consumed by the wrapped scenarios."""
        return self.get_previous_resources().get_previous_scenarios()

    def propagate_tags(
        self,
        tags: list[Tag],
        entity_tags_cache: dict[NavigableEntity, EntityTagList] | None = None,
        visited: set[NavigableEntity] | None = None,
    ) -> None:
        """Propagate tags from each wrapped scenario to its produced resources and attached notes,
        then recurse downstream. Origin is ``SCENARIO_PROPAGATED`` with the upstream scenario's id.
        See ``EntityNavigator.propagate_tags`` for the cache/visited contract."""
        if visited is None:
            visited = set()

        scenarios_to_walk = [s for s in self._entities if s not in visited]
        if not scenarios_to_walk:
            return
        visited.update(scenarios_to_walk)

        walker = EntityNavigatorScenario(scenarios_to_walk)

        # Propagate to resources (computed once for the whole batch)
        next_resources = walker.get_next_resources()
        for scenario in scenarios_to_walk:
            for resource in next_resources.get_entities_list():
                self._propagate_tags(
                    tags=tags,
                    entity=resource,
                    new_origin_type=TagOriginType.SCENARIO_PROPAGATED,
                    new_origin_id=scenario.id,
                    entity_tags_cache=entity_tags_cache,
                )
        next_resources.propagate_tags(tags, entity_tags_cache, visited)

        # Propagate to notes (computed once for the whole batch)
        next_notes = walker.get_next_notes()
        for scenario in scenarios_to_walk:
            for note in next_notes.get_entities_list():
                self._propagate_tags(
                    tags=tags,
                    entity=note,
                    new_origin_type=TagOriginType.SCENARIO_PROPAGATED,
                    new_origin_id=scenario.id,
                    entity_tags_cache=entity_tags_cache,
                )
        next_notes.propagate_tags(tags, entity_tags_cache, visited)

    def delete_propagated_tags(
        self,
        tags: list[Tag],
        entity_tags_cache: dict[NavigableEntity, EntityTagList] | None = None,
        visited: set[NavigableEntity] | None = None,
    ):
        """Inverse of ``propagate_tags`` for scenario edges: remove ``SCENARIO_PROPAGATED``
        copies from produced resources and attached notes, then recurse downstream."""
        if visited is None:
            visited = set()

        scenarios_to_walk = [s for s in self._entities if s not in visited]
        if not scenarios_to_walk:
            return
        visited.update(scenarios_to_walk)

        walker = EntityNavigatorScenario(scenarios_to_walk)

        next_resources = walker.get_next_resources()
        for scenario in scenarios_to_walk:
            for resource in next_resources.get_entities_list():
                self._delete_propagated_tags(
                    tags=tags,
                    entity=resource,
                    origin_type=TagOriginType.SCENARIO_PROPAGATED,
                    origin_id=scenario.id,
                    entity_tags_cache=entity_tags_cache,
                )
        next_resources.delete_propagated_tags(tags, entity_tags_cache, visited)

        next_notes = walker.get_next_notes()
        for scenario in scenarios_to_walk:
            for note in next_notes.get_entities_list():
                self._delete_propagated_tags(
                    tags=tags,
                    entity=note,
                    origin_type=TagOriginType.SCENARIO_PROPAGATED,
                    origin_id=scenario.id,
                    entity_tags_cache=entity_tags_cache,
                )
        next_notes.delete_propagated_tags(tags, entity_tags_cache, visited)


class EntityNavigatorResource(EntityNavigator[ResourceModel]):
    """Navigator over resources. Edges: resource -> views built from it,
    resource -> next resources via consuming tasks, resource -> consuming scenarios."""

    def get_next_notes(self) -> "EntityNavigatorNote":
        """Return notes attached to the views of the wrapped resources."""
        return self.get_next_views().get_next_notes()

    def get_next_views(self) -> "EntityNavigatorView":
        """Return views configured against the wrapped resources."""
        views = set(ViewConfig.get_by_resources(self._get_entities_ids()))
        return EntityNavigatorView(views)

    def get_next_resources(self) -> "EntityNavigatorResource":
        """Return resources produced by tasks that consume the wrapped resources as input."""
        tasks_model = self._get_next_tasks()

        task_model_ids = [task.id for task in tasks_model]

        resources = set(ResourceModel.get_by_task_models(task_model_ids))

        return EntityNavigatorResource(resources)

    def _get_next_tasks(self) -> set[TaskModel]:
        # retrieve all the tasks that uses the resource as input
        # Don't retrieve the input task that uses this resource as Config because the output of the input task
        # is the resource itself
        task_input_models: set[TaskInputModel] = set(
            TaskInputModel.get_by_resource_models(self._get_entities_ids())
        )
        return {task_input.task_model for task_input in task_input_models}

    def get_next_scenarios(self) -> "EntityNavigatorScenario":
        """Return all the scenarios that use the resource in a source task or as input of a task

        A scenario is considered a "next" scenario if it consumes (uses as input) any resource
        from this set. Scenarios that only produced resources in this set are excluded, unless
        they also consume resources produced by a different scenario in the set (which happens
        when resources from multiple scenarios are batched together).
        """
        return EntityNavigatorScenario(list(self.get_next_scenarios_select_model()))

    def get_next_scenarios_select_model(self) -> ModelSelect:
        """Return all the scenarios that use the resource in a source task or as input of a task"""
        expression = (TaskInputModel.resource_model.in_(self._get_entities_ids())) | (
            TaskModel.source_config_id.in_(self._get_entities_ids())
        )

        # Build a map of scenario_id -> resource_ids it produced in this set
        scenario_resource_map: dict[str, set[str]] = {}
        for resource in self._entities:
            if resource.scenario is not None:
                scenario_resource_map.setdefault(resource.scenario.id, set()).add(resource.id)

        # Exclude scenarios that only produced resources in this set but don't consume
        # any other resources from the set. A scenario that both produces AND consumes
        # resources in this set should not be excluded.
        resource_ids_set = set(self._get_entities_ids())
        exclude_scenario_ids: set[str] = set()
        for scenario_id, produced_ids in scenario_resource_map.items():
            # Resources in the set that this scenario did NOT produce
            consumed_ids = resource_ids_set - produced_ids
            if len(consumed_ids) == 0:
                # This scenario only produced resources in the set, exclude it
                exclude_scenario_ids.add(scenario_id)

        if len(exclude_scenario_ids) > 0:
            expression = expression & (Scenario.id.not_in(exclude_scenario_ids))

        # Search scenario where an input task is configured with the resource and where a task takes the resource as input
        # with this, all case are managed
        return (
            Scenario.select()
            .where(expression)
            .join(TaskInputModel, JOIN.LEFT_OUTER)
            .join(TaskModel, JOIN.LEFT_OUTER, on=(Scenario.id == TaskModel.scenario))
            .distinct()
        )

    def get_previous_resources(self) -> "EntityNavigatorResource":
        """Return resources consumed as input by the tasks that produced the wrapped resources."""
        # retrieve the tasks that generated the current resources
        task_model_ids = [
            resource.task_model.id for resource in self._entities if resource.task_model is not None
        ]

        # retrieve all the inputs of the tasks
        task_input_model: list[TaskInputModel] = list(
            TaskInputModel.get_by_task_models(task_model_ids)
        )

        resources = {task_input.resource_model for task_input in task_input_model}

        return EntityNavigatorResource(resources)

    def get_previous_scenarios(self) -> "EntityNavigatorScenario":
        """Return the scenarios that generated the wrapped resources."""
        scenario_ids: list[str] = [
            resource.scenario.id for resource in self._entities if resource.scenario is not None
        ]

        scenarios: set[Scenario] = set(Scenario.get_by_ids(scenario_ids))

        return EntityNavigatorScenario(scenarios)

    def propagate_tags(
        self,
        tags: list[Tag],
        entity_tags_cache: dict[NavigableEntity, EntityTagList] | None = None,
        visited: set[NavigableEntity] | None = None,
    ) -> None:
        """Propagate tags along two edge kinds and recurse:

        - resource -> view, with origin ``RESOURCE_PROPAGATED`` carrying the upstream resource's id;
        - resource -> next resource, with origin ``TASK_PROPAGATED`` carrying the producing task's id.

        See ``EntityNavigator.propagate_tags`` for the cache/visited contract.
        """
        if visited is None:
            visited = set()

        resources_to_walk = [r for r in self._entities if r not in visited]
        if not resources_to_walk:
            return
        visited.update(resources_to_walk)

        walker = EntityNavigatorResource(resources_to_walk)

        # Propagate to next views (computed once for the whole batch)
        next_views = walker.get_next_views()
        for resource in resources_to_walk:
            for view in next_views.get_entities_list():
                self._propagate_tags(
                    tags=tags,
                    entity=view,
                    new_origin_type=TagOriginType.RESOURCE_PROPAGATED,
                    new_origin_id=resource.id,
                    entity_tags_cache=entity_tags_cache,
                )
        next_views.propagate_tags(tags, entity_tags_cache, visited)

        # Propagate to next resources (computed once for the whole batch)
        next_resources = walker.get_next_resources()
        for next_resource in next_resources.get_entities_list():
            if next_resource.task_model:
                self._propagate_tags(
                    tags=tags,
                    entity=next_resource,
                    new_origin_type=TagOriginType.TASK_PROPAGATED,
                    new_origin_id=next_resource.task_model.id,
                    entity_tags_cache=entity_tags_cache,
                )
        next_resources.propagate_tags(tags, entity_tags_cache, visited)

    def delete_propagated_tags(
        self,
        tags: list[Tag],
        entity_tags_cache: dict[NavigableEntity, EntityTagList] | None = None,
        visited: set[NavigableEntity] | None = None,
    ):
        """Inverse of ``propagate_tags`` for resource edges: remove ``RESOURCE_PROPAGATED`` copies
        from views and ``TASK_PROPAGATED`` copies from next resources, then recurse downstream."""
        if visited is None:
            visited = set()

        resources_to_walk = [r for r in self._entities if r not in visited]
        if not resources_to_walk:
            return
        visited.update(resources_to_walk)

        walker = EntityNavigatorResource(resources_to_walk)

        next_views = walker.get_next_views()
        for resource in resources_to_walk:
            for view in next_views.get_entities_list():
                self._delete_propagated_tags(
                    tags=tags,
                    entity=view,
                    origin_type=TagOriginType.RESOURCE_PROPAGATED,
                    origin_id=resource.id,
                    entity_tags_cache=entity_tags_cache,
                )
        next_views.delete_propagated_tags(tags, entity_tags_cache, visited)

        next_resources = walker.get_next_resources()
        for next_resource in next_resources.get_entities_list():
            if next_resource.task_model:
                self._delete_propagated_tags(
                    tags=tags,
                    entity=next_resource,
                    origin_type=TagOriginType.TASK_PROPAGATED,
                    origin_id=next_resource.task_model.id,
                    entity_tags_cache=entity_tags_cache,
                )
        next_resources.delete_propagated_tags(tags, entity_tags_cache, visited)


class EntityNavigatorView(EntityNavigator[ViewConfig]):
    """Navigator over views. Edges: view -> notes embedding it; upstream is the view's resource."""

    def get_next_notes(self) -> "EntityNavigatorNote":
        """Return notes that embed any of the wrapped views via ``NoteViewModel``."""
        note_views: list[NoteViewModel] = list(NoteViewModel.get_by_views(self._get_entities_ids()))

        notes = {note_view.note for note_view in note_views}

        return EntityNavigatorNote(notes)

    def get_previous_resources(self) -> "EntityNavigatorResource":
        """Return the resources that the wrapped views are configured against."""
        resource_ids: list[str] = [
            view.resource_model.id for view in self._entities if view.resource_model is not None
        ]

        resources = set(ResourceModel.get_by_ids(resource_ids))

        return EntityNavigatorResource(resources)

    def get_previous_scenarios(self) -> "EntityNavigatorScenario":
        """Return the scenarios that produced the resources of the wrapped views."""
        return self.get_previous_resources().get_previous_scenarios()

    def _get_resources(self) -> list[ResourceModel]:
        return [view.resource_model for view in self._entities]

    def propagate_tags(
        self,
        tags: list[Tag],
        entity_tags_cache: dict[NavigableEntity, EntityTagList] | None = None,
        visited: set[NavigableEntity] | None = None,
    ) -> None:
        """Propagate tags from each wrapped view to the notes embedding it, then recurse.
        Origin is ``VIEW_PROPAGATED`` carrying the upstream view's id.
        See ``EntityNavigator.propagate_tags`` for the cache/visited contract."""
        if visited is None:
            visited = set()

        views_to_walk = [v for v in self._entities if v not in visited]
        if not views_to_walk:
            return
        visited.update(views_to_walk)

        walker = EntityNavigatorView(views_to_walk)

        next_notes = walker.get_next_notes()
        for view in views_to_walk:
            for note in next_notes.get_entities_list():
                self._propagate_tags(
                    tags=tags,
                    entity=note,
                    new_origin_type=TagOriginType.VIEW_PROPAGATED,
                    new_origin_id=view.id,
                    entity_tags_cache=entity_tags_cache,
                )
        next_notes.propagate_tags(tags, entity_tags_cache, visited)

    def delete_propagated_tags(
        self,
        tags: list[Tag],
        entity_tags_cache: dict[NavigableEntity, EntityTagList] | None = None,
        visited: set[NavigableEntity] | None = None,
    ):
        """Inverse of ``propagate_tags`` for view edges: remove ``VIEW_PROPAGATED`` copies
        from notes embedding the wrapped views."""
        if visited is None:
            visited = set()

        views_to_walk = [v for v in self._entities if v not in visited]
        if not views_to_walk:
            return
        visited.update(views_to_walk)

        walker = EntityNavigatorView(views_to_walk)

        next_notes = walker.get_next_notes()
        for view in views_to_walk:
            for note in next_notes.get_entities_list():
                self._delete_propagated_tags(
                    tags=tags,
                    entity=note,
                    origin_type=TagOriginType.VIEW_PROPAGATED,
                    origin_id=view.id,
                    entity_tags_cache=entity_tags_cache,
                )
        next_notes.delete_propagated_tags(tags, entity_tags_cache, visited)


class EntityNavigatorNote(EntityNavigator[Note]):
    """Navigator over notes. Notes are leaves of the lineage graph -- they have
    no downstream entities and therefore inherit the no-op ``propagate_tags``
    from the base class."""

    def get_previous_views(self) -> "EntityNavigatorView":
        """Return the views embedded in the wrapped notes via ``NoteViewModel``."""
        note_views: list[NoteViewModel] = list(NoteViewModel.get_by_notes(self._get_entities_ids()))

        return EntityNavigatorView({note_view.view for note_view in note_views})

    def get_previous_resources(self) -> "EntityNavigatorResource":
        """Return the resources backing the views embedded in the wrapped notes."""
        return self.get_previous_views().get_previous_resources()

    def get_previous_scenarios(self) -> "EntityNavigatorScenario":
        """Return the scenarios that produced the resources of the views in the wrapped notes."""
        return self.get_previous_resources().get_previous_scenarios()


class EntityNavigatorFormTemplate(EntityNavigator[FormTemplate]):
    """Navigator over form templates. Single edge: template -> forms bound via
    FormTemplateVersion.

    Not part of the lineage DAG used by ``get_next_entities_recursive`` and the
    other multi-type traversals -- forms are a separate template-binding edge.
    Reachable only via ``EntityNavigator.from_entity_id``.

    Filters on ``Tag.is_propagable`` internally: only propagable tags reach
    Forms, regardless of caller. This is stricter than ``EntityNavigatorScenario``
    & friends (which trust the caller) and matches the spec invariant:
    "non-propagable tags don't copy" (form_implementation_plan.md Phase 4).
    """

    def get_next_forms(self) -> "EntityNavigatorForm":
        """Return all Forms bound to any version of the wrapped templates."""
        forms: set[Form] = set()
        for template in self._entities:
            forms.update(Form.find_by_template(template.id))
        return EntityNavigatorForm(forms)

    def propagate_tags(
        self,
        tags: list[Tag],
        entity_tags_cache: dict[NavigableEntity, EntityTagList] | None = None,
        visited: set[NavigableEntity] | None = None,
    ) -> None:
        """Propagate tags to every Form bound to the wrapped templates with
        origin ``FORM_TEMPLATE_PROPAGATED`` (origin_id = template.id). Forms
        are leaves -- recursion bottoms out at ``EntityNavigatorForm``.

        Only propagable tags are forwarded; non-propagable tags are dropped
        per the Phase 4 spec invariant."""
        if visited is None:
            visited = set()

        templates_to_walk = [t for t in self._entities if t not in visited]
        if not templates_to_walk:
            return
        visited.update(templates_to_walk)

        propagable = [t for t in tags if t.is_propagable]
        if not propagable:
            return

        for template in templates_to_walk:
            forms = Form.find_by_template(template.id)
            for form in forms:
                self._propagate_tags(
                    tags=propagable,
                    entity=form,
                    new_origin_type=TagOriginType.FORM_TEMPLATE_PROPAGATED,
                    new_origin_id=template.id,
                    entity_tags_cache=entity_tags_cache,
                )
            EntityNavigatorForm(forms).propagate_tags(
                propagable, entity_tags_cache, visited
            )

    def delete_propagated_tags(
        self,
        tags: list[Tag],
        entity_tags_cache: dict[NavigableEntity, EntityTagList] | None = None,
        visited: set[NavigableEntity] | None = None,
    ):
        """Inverse of ``propagate_tags`` for the template->form edge: remove
        ``FORM_TEMPLATE_PROPAGATED`` copies from every Form bound to the
        wrapped templates."""
        if visited is None:
            visited = set()

        templates_to_walk = [t for t in self._entities if t not in visited]
        if not templates_to_walk:
            return
        visited.update(templates_to_walk)

        for template in templates_to_walk:
            forms = Form.find_by_template(template.id)
            for form in forms:
                self._delete_propagated_tags(
                    tags=tags,
                    entity=form,
                    origin_type=TagOriginType.FORM_TEMPLATE_PROPAGATED,
                    origin_id=template.id,
                    entity_tags_cache=entity_tags_cache,
                )
            EntityNavigatorForm(forms).delete_propagated_tags(
                tags, entity_tags_cache, visited
            )


class EntityNavigatorForm(EntityNavigator[Form]):
    """Navigator over forms. Forms are leaves of the template->form edge --
    they have no downstream entities and therefore inherit the no-op
    ``propagate_tags`` / ``delete_propagated_tags`` from the base class
    (same shape as ``EntityNavigatorNote``)."""
