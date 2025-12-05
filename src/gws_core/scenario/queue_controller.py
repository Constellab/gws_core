
from fastapi import Depends

from gws_core.scenario.queue_dto import JobDTO
from gws_core.scenario.queue_service import QueueService
from gws_core.scenario.scenario_dto import ScenarioDTO
from gws_core.user.authorization_service import AuthorizationService

from ..core_controller import core_app


@core_app.get("/queue/jobs", tags=["Queue"], summary="Get the list of job of main queue")
def get_the_scenario_queue(_=Depends(AuthorizationService.check_user_access_token)) -> list[JobDTO]:
    """
    Retrieve the queue of scenarios
    """

    queue_job = QueueService.get_queue_jobs()
    return [job.to_dto() for job in queue_job]


@core_app.delete("/queue/scenario/{id}", tags=["Queue"], summary="Get the queue of scenarios")
def remove_scenario_from_queue(
    id: str, _=Depends(AuthorizationService.check_user_access_token)
) -> ScenarioDTO:
    """
    Remove a scenario from the queue
    """

    return QueueService.remove_scenario_from_queue(id).to_dto()
