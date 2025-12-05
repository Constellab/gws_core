
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.entity_navigator.entity_navigator import (
    EntityNavigator,
    EntityNavigatorResource,
    EntityNavigatorScenario,
)
from gws_core.entity_navigator.entity_navigator_deep import NavigableEntitySet
from gws_core.entity_navigator.entity_navigator_dto import ImpactResult
from gws_core.entity_navigator.entity_navigator_type import NavigableEntityType
from gws_core.note.note import Note
from gws_core.note.note_service import NoteService
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.protocol.protocol_update import ProtocolUpdate
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_service import ResourceService
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_exception import (
    ResourceUnknownUsedInAnotherScenarioException,
    ResourceUnknownUsedInNoteException,
)
from gws_core.scenario.scenario_service import ScenarioService


class EntityNavigatorService:
    """Global service to manage route that have impact on multiple entities with scenario chain

    It is used to reset or delete a scenario, a resource or a process of a protocol
    """

    ############################################# SCENARIO #############################################

    @classmethod
    @GwsCoreDbManager.transaction()
    def check_impact_for_scenario_reset(cls, id_: str) -> ImpactResult:
        scenario: Scenario = Scenario.get_by_id_and_check(id_)

        return cls._calculate_scenario_reset_impact(scenario)

    @classmethod
    @GwsCoreDbManager.transaction()
    def reset_scenario(cls, id_: str) -> Scenario:
        scenario: Scenario = Scenario.get_by_id_and_check(id_)

        impact = cls._calculate_scenario_reset_impact(scenario)
        cls._delete_next_entities(impact.impacted_entities)

        return ScenarioService.reset_scenario(scenario)

    @classmethod
    @GwsCoreDbManager.transaction()
    def delete_scenario(cls, scenario_id: str) -> None:
        """Delete the scenario"""
        cls.reset_scenario(scenario_id)

        ScenarioService.delete_scenario(scenario_id)

    @classmethod
    def _calculate_scenario_reset_impact(cls, scenario: Scenario) -> ImpactResult:
        """Method to calculate the impact of the reset of a scenario.

        :param scenario: _description_
        :type scenario: Scenario
        :return: _description_
        :rtype: ImpactResult
        """
        scenario.check_is_updatable()
        exp_nav = EntityNavigatorScenario(scenario)
        return cls._calculate_impact(exp_nav)

    ############################################# PROCESS #############################################

    @classmethod
    @GwsCoreDbManager.transaction()
    def check_impact_for_process_reset(
        cls, protocol_id: str, process_instance_name: str
    ) -> ImpactResult:
        """Reset the process of a protocol. To check the impacted entities,
        it check the next entities of the scenario of the protocol

        """

        protocol_model = ProtocolService.get_by_id_and_check(protocol_id)
        protocol_model.check_is_updatable(error_if_finished=False)

        return cls._calculate_scenario_reset_impact(protocol_model.scenario)

    @classmethod
    @GwsCoreDbManager.transaction()
    def reset_process_of_protocol_id(
        cls, protocol_id: str, process_instance_name: str
    ) -> ProtocolUpdate:
        """Reset the process of a protocol. To check the impacted entities,
        it check the next entities of the scenario of the protocol

        """

        protocol_model = ProtocolService.get_by_id_and_check(protocol_id)
        protocol_model.check_is_updatable(error_if_finished=False)

        impact_result = cls._calculate_scenario_reset_impact(protocol_model.scenario)

        cls._delete_next_entities(impact_result.impacted_entities)

        return ProtocolService.reset_process_of_protocol(protocol_model, process_instance_name)

    @classmethod
    @GwsCoreDbManager.transaction()
    def reset_error_processes_of_protocol(cls, protocol_model: ProtocolModel) -> None:
        """Specific method to reset all the error process of a protocol.

        There is no force option and if there are some impacted entities, it will raise an error
        """
        protocol_model.check_is_updatable(error_if_finished=False)

        # check if there are some scenario that use the result of the scenario
        reset_result = cls._calculate_scenario_reset_impact(protocol_model.scenario)

        # if yes, raise an error, no force reset for this mode
        if reset_result.has_entities():
            scenarios: list[Scenario] = reset_result.impacted_entities.get_entity_by_type(
                NavigableEntityType.SCENARIO
            )

            if len(scenarios) > 0:
                raise ResourceUnknownUsedInAnotherScenarioException(
                    scenarios[0].get_short_name(), scenarios[0].id
                )

            notes: list[Note] = reset_result.impacted_entities.get_entity_by_type(
                NavigableEntityType.NOTE
            )
            if len(notes) > 0:
                raise ResourceUnknownUsedInNoteException(notes[0].title, notes[0].id)

            raise BadRequestException(
                "Can't reset the process because the scenario output is used elsewhere"
            )

        # reset all the error processes
        error_tasks = protocol_model.get_error_tasks()
        for task in error_tasks:
            ProtocolService.reset_process_of_protocol(task.parent_protocol, task.instance_name)

        protocol_model.refresh_status()

    ############################################# RESOURCE #############################################

    @classmethod
    @GwsCoreDbManager.transaction()
    def check_impact_delete_resource(cls, resource_id: str) -> ImpactResult:
        resource = ResourceService.get_by_id_and_check(resource_id)

        # If the resource was generated by a scenario, reset the scenario
        if resource.scenario:
            exp_nav = EntityNavigatorScenario(resource.scenario)
            # include the scenario that generated the resource in the impact
            return cls._calculate_impact(exp_nav, include_current_entities=True)
        else:
            resource_nav = EntityNavigatorResource(resource)
            return cls._calculate_impact(resource_nav)

    @classmethod
    @GwsCoreDbManager.transaction()
    def delete_resource(cls, resource_id: str, allow_s3_folder_storage: bool = False) -> None:
        """Delete the resource"""

        resource = ResourceService.get_by_id_and_check(resource_id)

        if resource.origin == ResourceOrigin.S3_FOLDER_STORAGE and not allow_s3_folder_storage:
            raise BadRequestException("Cannot delete the resource because it is an S3 resource")

        # If the resource was generated by a scenario, reset the scenario
        if resource.scenario:
            # call delete scenario
            cls.delete_scenario(resource.scenario.id)
        else:
            resource_nav = EntityNavigatorResource(resource)
            result = cls._calculate_impact(resource_nav)
            cls._delete_next_entities(result.impacted_entities)

            ResourceService.delete(resource_id)

    ############################################# OTHERS #############################################

    @classmethod
    def _calculate_impact(
        cls, entity_navigator: EntityNavigator, include_current_entities: bool = False
    ) -> ImpactResult:
        """Method to calculate the impact of the reset of a scenario.

        :param scenario: _description_
        :type scenario: Scenario
        :return: _description_
        :rtype: ImpactResult
        """
        next_entities = entity_navigator.get_next_entities_recursive(
            [NavigableEntityType.SCENARIO, NavigableEntityType.NOTE],
            include_current_entities=include_current_entities,
        )

        return ImpactResult(impacted_entities=next_entities)

    @classmethod
    @GwsCoreDbManager.transaction()
    def _delete_next_entities(cls, entities: NavigableEntitySet) -> None:
        """Delete the entities"""
        cls._check_validated_entities(
            entities, [NavigableEntityType.SCENARIO, NavigableEntityType.NOTE]
        )

        notes = entities.get_entities_from_deepest_level(NavigableEntityType.NOTE)
        for note in notes:
            NoteService.delete(note.id)

        # TODO to improve because this is not perfect if I have 3 scenario.
        # Exp 1: output --> A
        # Exp 2: input --> A, output --> B
        # Exp 3: input --> A, B
        # In this case the Exp 3 will have the same deep level as the Exp 2
        scenarios = entities.get_entities_from_deepest_level(NavigableEntityType.SCENARIO)
        for scenario in scenarios:
            ScenarioService.delete_scenario(scenario.id)

    @classmethod
    def _check_validated_entities(
        cls, entities: NavigableEntitySet, entity_types: list[NavigableEntityType]
    ) -> None:
        """Check if there are some validated entities in the set"""
        for entity_type in entity_types:
            # check if any of the next scenario is validated
            validated_entities = [
                entity
                for entity in entities.get_entity_by_type(entity_type)
                if entity.navigable_entity_is_validated()
            ]

            if len(validated_entities) > 0:
                # get the title of max 3 validated scenarios
                validated_entities_titles = [
                    entity.get_navigable_entity_name() for entity in validated_entities[:3]
                ]

                entity_type_human_name = entity_type.get_human_name(plurial=True)
                raise BadRequestException(
                    f"Cannot reset the scenario because there is {len(validated_entities)} validated {entity_type_human_name} that are linked to this scenario. Here are some of the link {entity_type_human_name}: {validated_entities_titles}"
                )
