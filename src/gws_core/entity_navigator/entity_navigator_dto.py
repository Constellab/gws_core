# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.entity_navigator.entity_navigator_type import (
    EntityNavGroupDTO, NavigableEntitySet)
from gws_core.experiment.experiment_dto import ExperimentDTO
from gws_core.protocol.protocol_dto import ProtocolUpdateDTO
from gws_core.resource.resource_dto import ResourceDTO


class ImpactResult():
    success: bool
    impacted_entities: NavigableEntitySet[Any]

    def __init__(self, success: bool, impacted_entities: NavigableEntitySet[Any]):
        self.success = success
        self.impacted_entities = impacted_entities


class ResetExperimentResultDTO(BaseModelDTO):
    success: bool
    experiment: ExperimentDTO
    impacted_entities: Optional[List[EntityNavGroupDTO]] = None


class DeleteResourceResultDTO(BaseModelDTO):
    success: bool
    resource: ResourceDTO
    impacted_entities: Optional[List[EntityNavGroupDTO]] = None


class ProcessResetResultDTO(BaseModelDTO):
    success: bool
    protocol_update: Optional[ProtocolUpdateDTO] = None
    impacted_entities: Optional[List[EntityNavGroupDTO]] = None
