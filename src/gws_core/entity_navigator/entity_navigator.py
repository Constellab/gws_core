from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Generic, Literal, TypeVar

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

PropagationAction = Literal["add", "delete"]


@dataclass
class PropagationEdge:
    """Describes a single outgoing propagation edge for a navigator.

    ``downstream`` is the navigator wrapping the direct neighbors reached over
    this edge (computed once for the whole batch). ``origin_type`` is the
    ``TagOriginType`` to attach to tags propagated along this edge.

    ``origin_id_fn`` derives the origin id from the (upstream, downstream)
    pair. When omitted, the upstream entity's id is used -- this covers the
    common case (scenario->resource, view->note, etc.). The resource->resource
    edge overrides it to derive the origin from the downstream's producing
    task; returning ``None`` from the override skips the downstream entity
    (used when the producing task is missing).

    Redundant writes (same downstream reached from multiple upstreams with
    the same resulting origin) are filtered inside ``_apply_tags`` via the
    in-memory tag cache, so this struct does not need a per-downstream flag.
    """

    downstream: "EntityNavigator"
    origin_type: TagOriginType
    origin_id_fn: Callable[[NavigableEntity, NavigableEntity], str | None] = (
        lambda upstream, downstream: upstream.id
    )


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

    def get_next_forms(self) -> "EntityNavigatorForm":
        """Return the direct downstream forms. Empty by default; only
        ``EntityNavigatorFormTemplate`` overrides this -- forms sit on a
        separate template-binding edge that's not part of the four-type
        lineage DAG."""
        return EntityNavigatorForm(set())

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
        self._walk_propagation(tags, "add", entity_tags_cache, visited)

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
        self._walk_propagation(tags, "delete", entity_tags_cache, visited)

    def _iter_propagation_edges(
        self, walker: "EntityNavigator"
    ) -> Iterable[PropagationEdge]:
        """Yield the outgoing propagation edges for this navigator type.

        Each subclass overrides this to declare its edges. The default is no
        edges, which makes leaf navigators (notes, forms) no-op for propagation.

        ``walker`` is the navigator wrapping the not-yet-visited subset of
        ``self._entities`` -- subclasses use it to compute downstream sets
        once for the whole batch (``walker.get_next_resources()`` etc.).
        """
        return ()

    def _walk_propagation(
        self,
        tags: list[Tag],
        action: PropagationAction,
        entity_tags_cache: dict[NavigableEntity, EntityTagList] | None,
        visited: set[NavigableEntity] | None,
    ) -> None:
        """Template method: walk outgoing edges, apply ``action`` per edge, recurse.

        Shared skeleton between propagation and deletion. Subclasses customize
        only the edge list via ``_iter_propagation_edges``.
        """
        if visited is None:
            visited = set()

        to_walk = [e for e in self._entities if e not in visited]
        if not to_walk:
            return
        visited.update(to_walk)

        walker = self.__class__(to_walk)

        for edge in self._iter_propagation_edges(walker):
            downstream_list = edge.downstream.get_entities_list()
            for upstream in to_walk:
                for downstream in downstream_list:
                    origin_id = edge.origin_id_fn(upstream, downstream)
                    if origin_id is None:
                        continue
                    self._apply_tags(
                        tags=tags,
                        entity=downstream,
                        origin_type=edge.origin_type,
                        origin_id=origin_id,
                        action=action,
                        entity_tags_cache=entity_tags_cache,
                    )
            edge.downstream._walk_propagation(
                tags, action, entity_tags_cache, visited
            )

    def _apply_tags(
        self,
        tags: list[Tag],
        entity: NavigableEntity,
        origin_type: TagOriginType,
        origin_id: str,
        action: PropagationAction,
        entity_tags_cache: dict[NavigableEntity, EntityTagList] | None = None,
    ):
        """Add or delete a propagated copy of ``tags`` on a single ``entity``.

        Filters out tags that are no-ops against the in-memory ``EntityTagList``
        before touching the DB:

        - ``add``: skip tags already present on ``entity`` whose origin already
          contains ``(origin_type, origin_id)``. Both the lookup and the
          ``add_tag`` short-circuit at the application layer return early on a
          duplicate, but ``add_tags`` still opens a DB transaction per call --
          filtering here avoids that. For multi-origin entities (notes), an
          existing tag without this origin is *not* skipped, so origin merging
          via ``EntityTag.merge_tag`` still happens.
        - ``delete``: skip tags absent from ``entity``, or present but without
          this specific origin. Same rationale.

        ``entity`` is typed as ``NavigableEntity`` (not ``GenericNavigableEntity``)
        because propagation crosses entity types -- e.g. an
        ``EntityNavigatorScenario`` writes tags onto downstream resources and
        notes, not just scenarios.
        """
        if entity_tags_cache is None:
            entity_tags_cache = {}

        if entity not in entity_tags_cache:
            tag_type = entity.get_navigable_entity_type().convert_to_tag_entity_type()
            entity_tags_cache[entity] = EntityTagList.find_by_entity(tag_type, entity.id)

        entity_tags = entity_tags_cache[entity]

        propagated_tags = [tag.propagate(origin_type, origin_id) for tag in tags]
        effective_tags = [
            t for t in propagated_tags
            if self._needs_apply(entity_tags, t, origin_type, origin_id, action)
        ]
        if not effective_tags:
            return

        if action == "add":
            entity_tags.add_tags(effective_tags)
        else:
            entity_tags.delete_tags(effective_tags)

    @staticmethod
    def _needs_apply(
        entity_tags: EntityTagList,
        tag: Tag,
        origin_type: TagOriginType,
        origin_id: str,
        action: PropagationAction,
    ) -> bool:
        """Return True if applying ``action`` to ``tag`` on ``entity_tags`` would
        change state. Skips redundant DB writes when the same upstream-origin pair
        is reached more than once during a walk.

        For ``add``: the tag must either be missing, or present but missing this
        specific origin (so multi-origin merging still fires for notes).
        For ``delete``: the tag must be present *with* this specific origin.
        """
        existing = entity_tags.get_tag(tag)
        if action == "add":
            if existing is None:
                return True
            return not existing.get_origins().has_origin(origin_type, origin_id)
        # delete
        if existing is None:
            return False
        return existing.get_origins().has_origin(origin_type, origin_id)

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

    def _iter_propagation_edges(
        self, walker: "EntityNavigator"
    ) -> Iterable[PropagationEdge]:
        """scenario -> produced resources and attached notes, both with
        ``SCENARIO_PROPAGATED`` origin carrying the upstream scenario's id."""
        return [
            PropagationEdge(
                downstream=walker.get_next_resources(),
                origin_type=TagOriginType.SCENARIO_PROPAGATED,
            ),
            PropagationEdge(
                downstream=walker.get_next_notes(),
                origin_type=TagOriginType.SCENARIO_PROPAGATED,
            ),
        ]


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

    def _iter_propagation_edges(
        self, walker: "EntityNavigator"
    ) -> Iterable[PropagationEdge]:
        """Two outgoing edges:

        - resource -> view: ``RESOURCE_PROPAGATED`` carrying the upstream resource's id.
        - resource -> next resource: ``TASK_PROPAGATED`` carrying the *producing*
          task's id (derived from the downstream's ``task_model``). Returns
          ``None`` for downstream resources without a task model so they are
          skipped.

        Multiple upstreams can produce the same downstream over the
        resource->resource edge (e.g. a task with two input resources both
        in the walk). The base ``_apply_tags`` filters out duplicate writes
        via the in-memory tag cache, so the doubly-nested loop is safe.
        """
        return [
            PropagationEdge(
                downstream=walker.get_next_views(),
                origin_type=TagOriginType.RESOURCE_PROPAGATED,
            ),
            PropagationEdge(
                downstream=walker.get_next_resources(),
                origin_type=TagOriginType.TASK_PROPAGATED,
                origin_id_fn=self._task_propagation_origin_id,
            ),
        ]

    @staticmethod
    def _task_propagation_origin_id(
        upstream: NavigableEntity, downstream: NavigableEntity
    ) -> str | None:
        """Origin id for the resource->resource edge: the *downstream*'s
        producing task. Skip downstream entities that are not resources, or
        whose ``task_model`` is missing. ``upstream`` is unused -- when multiple
        upstreams produce the same ``(downstream, origin)`` triple, the
        in-memory cache check in ``_apply_tags`` short-circuits the redundant
        DB writes."""
        if not isinstance(downstream, ResourceModel):
            return None
        if downstream.task_model is None:
            return None
        return downstream.task_model.id


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

    def _iter_propagation_edges(
        self, walker: "EntityNavigator"
    ) -> Iterable[PropagationEdge]:
        """view -> notes embedding it, with ``VIEW_PROPAGATED`` origin
        carrying the upstream view's id."""
        return [
            PropagationEdge(
                downstream=walker.get_next_notes(),
                origin_type=TagOriginType.VIEW_PROPAGATED,
            ),
        ]


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

    Caller convention (matches ``EntityNavigatorScenario`` & friends): the
    caller -- typically ``TagService.add_tags_to_entity_and_propagate`` --
    is responsible for ensuring propagation only fires for propagable tags.
    The navigator does not re-filter.
    """

    def get_next_forms(self) -> "EntityNavigatorForm":
        """Return all Forms bound to any version of the wrapped templates."""
        forms: set[Form] = set()
        for template in self._entities:
            forms.update(Form.find_by_template(template.id))
        return EntityNavigatorForm(forms)

    def _iter_propagation_edges(
        self, walker: "EntityNavigator"
    ) -> Iterable[PropagationEdge]:
        """template -> forms bound to any of its versions, with
        ``FORM_TEMPLATE_PROPAGATED`` origin carrying the upstream template's id."""
        return [
            PropagationEdge(
                downstream=walker.get_next_forms(),
                origin_type=TagOriginType.FORM_TEMPLATE_PROPAGATED,
            ),
        ]


class EntityNavigatorForm(EntityNavigator[Form]):
    """Navigator over forms. Forms are leaves of the template->form edge --
    they have no downstream entities and therefore inherit the no-op
    ``propagate_tags`` / ``delete_propagated_tags`` from the base class
    (same shape as ``EntityNavigatorNote``)."""
