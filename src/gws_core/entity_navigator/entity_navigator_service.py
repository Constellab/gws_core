# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core.core.decorator.transaction import transaction
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.entity_navigator.entity_navigator import (
    EntityNavigatorExperiment, EntityNavigatorResource)
from gws_core.entity_navigator.entity_navigator_dto import (
    DeleteResourceResultDTO, ImpactResult, ProcessResetResultDTO,
    ResetExperimentResultDTO)
from gws_core.entity_navigator.entity_navigator_type import (
    EntityType, NavigableEntity, NavigableEntitySet)
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_exception import (
    ResourceUnknownUsedInAnotherExperimentException,
    ResourceUnknownUsedInReportException)
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.report.report import Report
from gws_core.report.report_service import ReportService
from gws_core.resource.resource_service import ResourceService


class EntityNavigatorService:
    """ Global service to manage route that have impact on multiple entities with experiment chain

    It is used to reset or delete an experiment, a resource or a process of a protocol
    """

    ############################################# EXPERIMENT #############################################

    @classmethod
    @transaction()
    def reset_experiment(cls, id_: str, force: bool) -> ResetExperimentResultDTO:
        experiment: Experiment = Experiment.get_by_id_and_check(id_)

        impacted_result = cls._get_experiment_reset_impact_result(experiment, force)

        if not impacted_result.success:
            return ResetExperimentResultDTO(
                success=False,
                experiment=experiment.to_dto(),
                impacted_entities=impacted_result.impacted_entities.get_entity_dict_nav_group()
            )

        experiment = ExperimentService.reset_experiment(experiment)
        return ResetExperimentResultDTO(
            success=True,
            experiment=experiment.to_dto(),
        )

    @classmethod
    @transaction()
    def delete_experiment(cls, experiment_id: str, force: bool) -> ResetExperimentResultDTO:
        """Delete the experiment
        """
        result = cls.reset_experiment(experiment_id, force)

        if result.success:
            ExperimentService.delete_experiment(experiment_id)

        return result

    @classmethod
    def _get_experiment_reset_impact_result(cls, experiment: Experiment, force: bool) -> ImpactResult:
        """Method to calculate the impact of the reset of an experiment. If force is True, it will
        delete the next entities

        :param experiment: _description_
        :type experiment: Experiment
        :param force: _description_
        :type force: bool
        :return: _description_
        :rtype: ImpactResult
        """
        exp_nav = EntityNavigatorExperiment(experiment)
        next_entities = exp_nav.get_next_entities_recursive([EntityType.EXPERIMENT, EntityType.REPORT])

        # check if there are some experiment that use the result of the experiment
        if len(next_entities) > 0:

            if not force:
                return ImpactResult(
                    success=False,
                    impacted_entities=next_entities
                )

            else:
                cls._delete_next_entities(next_entities)

        return ImpactResult(
            success=True,
            impacted_entities=next_entities
        )

    ############################################# PROCESS #############################################

    @classmethod
    @transaction()
    def reset_process_of_protocol_id(cls, protocol_id: str, process_instance_name: str,
                                     force: bool) -> ProcessResetResultDTO:
        """Reset the process of a protocol. To check the impacted entities,
        it check the next entities of the experiment of the protocol

        """

        protocol_model = ProtocolService.get_by_id_and_check(protocol_id)
        protocol_model.check_is_updatable(error_if_finished=False)

        impact_result = cls._get_experiment_reset_impact_result(protocol_model.experiment, force)

        if not impact_result.success:
            return ProcessResetResultDTO(
                success=False,
                impacted_entities=impact_result.impacted_entities.get_entity_dict_nav_group()
            )

        protocol_update = ProtocolService.reset_process_of_protocol(protocol_model, process_instance_name)
        return ProcessResetResultDTO(
            success=True,
            protocol_update=protocol_update.to_dto(),
        )

    @classmethod
    @transaction()
    def reset_error_processes_of_protocol(cls, protocol_model: ProtocolModel) -> None:
        """Specific method to reset all the error process of a protocol.

        There is no force option and if there are some impacted entities, it will raise an error
        """
        protocol_model.check_is_updatable(error_if_finished=False)

        # check if there are some experiment that use the result of the experiment
        reset_result = cls._get_experiment_reset_impact_result(protocol_model.experiment, False)

        # if yes, raise an error, no force reset for this mode
        if not reset_result.success:
            experiments: List[Experiment] = reset_result.impacted_entities.get_entity_by_type(EntityType.EXPERIMENT)
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
    def delete_resource(cls, resource_id: str, force: bool) -> DeleteResourceResultDTO:
        """Delete the resource
        """

        resource = ResourceService.get_by_id_and_check(resource_id)
        exp_nav = EntityNavigatorResource(resource)
        next_entities = exp_nav.get_next_entities_recursive([EntityType.EXPERIMENT, EntityType.REPORT])

        # check if there are some experiment that use the result of the experiment
        if len(next_entities) > 0:

            if not force:
                return DeleteResourceResultDTO(
                    success=False,
                    resource=resource.to_dto(),
                    impacted_entities=next_entities.get_entity_dict_nav_group()
                )
            else:
                cls._delete_next_entities(next_entities)

        # Check how to manage s3 resources
        ResourceService.delete(resource_id)
        return DeleteResourceResultDTO(
            success=True,
            resource=resource.to_dto(),
        )

    ############################################# OTHERS #############################################

    @classmethod
    @transaction()
    def _delete_next_entities(cls, entities: NavigableEntitySet[NavigableEntity]) -> None:
        """Delete the entities
        """
        cls._check_validated_entities(entities, [EntityType.EXPERIMENT, EntityType.REPORT])

        reports = entities.get_entity_by_type(EntityType.REPORT)
        for report in reports:
            ReportService.delete(report.id)

        experiments = entities.get_entity_by_type(EntityType.EXPERIMENT)
        for experiment in experiments:
            ExperimentService.delete_experiment(experiment.id)

    @classmethod
    def _check_validated_entities(
            cls, entities: NavigableEntitySet[NavigableEntity],
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
