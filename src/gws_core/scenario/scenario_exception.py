from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from gws_core.core.service.front_service import FrontService

from ..core.exception.exceptions.bad_request_exception import BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..process.process_exception import ProcessRunException

if TYPE_CHECKING:
    from .scenario import Scenario


class ScenarioRunException(BadRequestException):
    """Generic exception to raised from another exception during the process run
    It show the original error and provided debug information about the process and scenario

    :param BadRequestException: [description]
    :type BadRequestException: [type]
    """

    original_exception: Exception
    scenario: Scenario

    def __init__(
        self,
        scenario: Scenario,
        exception_detail: str,
        unique_code: str,
        instance_id: str,
        exception: Exception,
    ) -> None:
        self.original_exception = exception
        self.scenario = scenario

        detail_arg: Dict = {"error": exception_detail, "scenario": scenario.id}
        super().__init__(
            GWSException.SCENARIO_RUN_EXCEPTION.value,
            unique_code=unique_code,
            detail_args=detail_arg,
            instance_id=instance_id,
        )

    @staticmethod
    def from_exception(scenario: Scenario, exception: Exception) -> ScenarioRunException:
        unique_code: str
        instance_id: str

        # create from a know exception
        if isinstance(exception, ProcessRunException):
            unique_code = exception.unique_code
            instance_id = exception.instance_id
        else:
            unique_code = GWSException.SCENARIO_RUN_EXCEPTION.name
            instance_id = None

        return ScenarioRunException(
            scenario=scenario,
            exception_detail=str(exception),
            unique_code=unique_code,
            instance_id=instance_id,
            exception=exception,
        )


class ResourceUsedInAnotherScenarioException(BadRequestException):
    def __init__(
        self, resource_model_name: str, resource_id: str, scenario_name: str, scenario_id: str
    ) -> None:
        super().__init__(
            GWSException.RESET_ERROR_RESOURCE_USED_IN_ANOTHER_SCENARIO.value,
            unique_code=GWSException.RESET_ERROR_RESOURCE_USED_IN_ANOTHER_SCENARIO.name,
            detail_args={
                "resource_model_name": resource_model_name,
                "resource_url": FrontService.get_resource_url(resource_id),
                "scenario": scenario_name,
                "scenario_url": FrontService.get_scenario_url(scenario_id),
            },
        )


class ResourceUnknownUsedInAnotherScenarioException(BadRequestException):
    def __init__(self, scenario_name: str, scenario_id: str) -> None:
        super().__init__(
            GWSException.RESET_ERROR_EXP_LINKED_TO_IN_ANOTHER_EXP.value,
            unique_code=GWSException.RESET_ERROR_EXP_LINKED_TO_IN_ANOTHER_EXP.name,
            detail_args={
                "scenario": scenario_name,
                "scenario_url": FrontService.get_scenario_url(scenario_id),
            },
        )


class ResourceUnknownUsedInNoteException(BadRequestException):
    def __init__(self, note_name: str, note_id: str) -> None:
        super().__init__(
            GWSException.RESET_ERROR_EXP_LINKED_TO_IN_ANOTHER_EXP.value,
            unique_code=GWSException.RESET_ERROR_EXP_LINKED_TO_IN_ANOTHER_EXP.name,
            detail_args={"scenario": note_name, "scenario_url": FrontService.get_note_url(note_id)},
        )
