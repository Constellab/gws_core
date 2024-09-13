

from typing import List

from gws_core.core.decorator.transaction import transaction
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.entity_navigator.entity_navigator import (
    EntityNavigator, EntityNavigatorExperiment, EntityNavigatorResource)
from gws_core.entity_navigator.entity_navigator_deep import NavigableEntitySet
from gws_core.entity_navigator.entity_navigator_dto import ImpactResult
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_exception import (
    ResourceUnknownUsedInAnotherExperimentException,
    ResourceUnknownUsedInReportException)
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.protocol.protocol_update import ProtocolUpdate
from gws_core.report.report import Report
from gws_core.report.report_service import ReportService
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_service import ResourceService


class EntityNavigatorService:
    """ Global service to manage route that have impact on multiple entities with experiment chain

    It is used to reset or delete an experiment, a resource or a process of a protocol
    """

    ############################################# EXPERIMENT #############################################

    @classmethod
    @transaction()
    def check_impact_for_experiment_reset(cls, id_: str) -> ImpactResult:
        experiment: Experiment = Experiment.get_by_id_and_check(id_)

        return cls._calculate_experiment_reset_impact(experiment)

    @classmethod
    @transaction()
    def reset_experiment(cls, id_: str) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id_)

        impact = cls._calculate_experiment_reset_impact(experiment)
        cls._delete_next_entities(impact.impacted_entities)

        return ExperimentService.reset_experiment(experiment)

    @classmethod
    @transaction()
    def delete_experiment(cls, experiment_id: str) -> None:
        """Delete the experiment
        """
        cls.reset_experiment(experiment_id)

        ExperimentService.delete_experiment(experiment_id)

    @classmethod
    def _calculate_experiment_reset_impact(cls, experiment: Experiment) -> ImpactResult:
        """Method to calculate the impact of the reset of an experiment.

        :param experiment: _description_
        :type experiment: Experiment
        :return: _description_
        :rtype: ImpactResult
        """
        experiment.check_is_updatable()
        exp_nav = EntityNavigatorExperiment(experiment)
        return cls._calculate_impact(exp_nav)

    ############################################# PROCESS #############################################

    @classmethod
    @transaction()
    def check_impact_for_process_reset(cls, protocol_id: str, process_instance_name: str) -> ImpactResult:
        """Reset the process of a protocol. To check the impacted entities,
        it check the next entities of the experiment of the protocol

        """

        protocol_model = ProtocolService.get_by_id_and_check(protocol_id)
        protocol_model.check_is_updatable(error_if_finished=False)

        return cls._calculate_experiment_reset_impact(protocol_model.experiment)

    @classmethod
    @transaction()
    def reset_process_of_protocol_id(cls, protocol_id: str, process_instance_name: str) -> ProtocolUpdate:
        """Reset the process of a protocol. To check the impacted entities,
        it check the next entities of the experiment of the protocol

        """

        protocol_model = ProtocolService.get_by_id_and_check(protocol_id)
        protocol_model.check_is_updatable(error_if_finished=False)

        impact_result = cls._calculate_experiment_reset_impact(protocol_model.experiment)

        cls._delete_next_entities(impact_result.impacted_entities)

        return ProtocolService.reset_process_of_protocol(protocol_model, process_instance_name)

    @classmethod
    @transaction()
    def reset_error_processes_of_protocol(cls, protocol_model: ProtocolModel) -> None:
        """Specific method to reset all the error process of a protocol.

        There is no force option and if there are some impacted entities, it will raise an error
        """
        protocol_model.check_is_updatable(error_if_finished=False)

        # check if there are some experiment that use the result of the experiment
        reset_result = cls._calculate_experiment_reset_impact(protocol_model.experiment)

        # if yes, raise an error, no force reset for this mode
        if reset_result.has_entities():
            experiments: List[Experiment] = reset_result.impacted_entities.get_entity_by_type(
                EntityType.EXPERIMENT)

            if len(experiments) > 0:
                raise ResourceUnknownUsedInAnotherExperimentException(
                    experiments[0].get_short_name(), experiments[0].id)

            reports: List[Report] = reset_result.impacted_entities.get_entity_by_type(EntityType.REPORT)
            if len(reports) > 0:
                raise ResourceUnknownUsedInReportException(reports[0].title, reports[0].id)

            raise BadRequestException(
                "Can't reset the process because the experiment output is used elsewhere")

        # reset all the error processes
        error_tasks = protocol_model.get_error_tasks()
        for task in error_tasks:
            ProtocolService.reset_process_of_protocol(task.parent_protocol, task.instance_name)

    ############################################# RESOURCE #############################################

    @classmethod
    @transaction()
    def check_impact_delete_resource(cls, resource_id: str) -> ImpactResult:
        resource = ResourceService.get_by_id_and_check(resource_id)

        # If the resource was generated by an experiment, reset the experiment
        if resource.experiment:
            exp_nav = EntityNavigatorExperiment(resource.experiment)
            # include the experiment that generated the resource in the impact
            return cls._calculate_impact(exp_nav, include_current_entities=True)
        else:
            resource_nav = EntityNavigatorResource(resource)
            return cls._calculate_impact(resource_nav)

    @classmethod
    @transaction()
    def delete_resource(cls, resource_id: str, allow_s3_folder_storage: bool = False) -> None:
        """Delete the resource
        """

        resource = ResourceService.get_by_id_and_check(resource_id)

        if resource.origin == ResourceOrigin.S3_FOLDER_STORAGE and not allow_s3_folder_storage:
            raise BadRequestException(
                "Cannot delete the resource because it is an S3 resource")

        # If the resource was generated by an experiment, reset the experiment
        if resource.experiment:
            # call delete experiment
            cls.delete_experiment(resource.experiment.id)
        else:
            resource_nav = EntityNavigatorResource(resource)
            result = cls._calculate_impact(resource_nav)
            cls._delete_next_entities(result.impacted_entities)

            ResourceService.delete(resource_id)

    ############################################# OTHERS #############################################

    @classmethod
    def _calculate_impact(
            cls, entity_navigator: EntityNavigator, include_current_entities: bool = False) -> ImpactResult:
        """Method to calculate the impact of the reset of an experiment.

        :param experiment: _description_
        :type experiment: Experiment
        :return: _description_
        :rtype: ImpactResult
        """
        next_entities = entity_navigator.get_next_entities_recursive(
            [EntityType.EXPERIMENT, EntityType.REPORT], include_current_entities=include_current_entities)

        return ImpactResult(
            impacted_entities=next_entities
        )

    @classmethod
    @transaction()
    def _delete_next_entities(cls, entities: NavigableEntitySet) -> None:
        """Delete the entities
        """
        cls._check_validated_entities(entities, [EntityType.EXPERIMENT, EntityType.REPORT])

        reports = entities.get_entities_from_deepest_level(EntityType.REPORT)
        for report in reports:
            ReportService.delete(report.id)

        # TODO to improve because this is not perfect if I have 3 experiment.
        # Exp 1: output --> A
        # Exp 2: input --> A, output --> B
        # Exp 3: input --> A, B
        # In this case the Exp 3 will have the same deep level as the Exp 2
        experiments = entities.get_entities_from_deepest_level(EntityType.EXPERIMENT)
        for experiment in experiments:
            ExperimentService.delete_experiment(experiment.id)

    @classmethod
    def _check_validated_entities(
            cls, entities: NavigableEntitySet,
            entity_types: List[EntityType]) -> None:
        """Check if there are some validated entities in the set
        """
        for entity_type in entity_types:
            # check if any of the next experiment is validated
            validated_entities = [entity for entity in entities.get_entity_by_type(
                entity_type) if entity.entity_is_validated()]

            if len(validated_entities) > 0:
                # get the title of max 3 validated experiments
                validated_entities_titles = [entity.get_entity_name() for entity in validated_entities[:3]]

                entity_type_human_name = EntityType.get_human_name(entity_type, plurial=True)
                raise BadRequestException(
                    f"Cannot reset the experiment because there is {len(validated_entities)} validated {entity_type_human_name} that are linked to this experiment. Here are some of the link {entity_type_human_name}: {validated_entities_titles}")
