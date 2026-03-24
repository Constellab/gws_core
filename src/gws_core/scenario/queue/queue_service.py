from gws_core.core.exception.exceptions import BadRequestException, NotFoundException
from gws_core.entity_navigator.entity_navigator_service import EntityNavigatorService
from gws_core.scenario.queue.queue import Job
from gws_core.scenario.queue.queue_runner import QueueRunner
from gws_core.scenario.scenario import Scenario
from gws_core.user.current_user_service import CurrentUserService


class QueueService:
    """Pure queue operations service.

    Handles adding/removing jobs. Can be called from any process (main or sub).
    No process awareness, no tick loop, no threading.
    """

    @classmethod
    def add_scenario_to_queue(cls, scenario_id: str) -> Scenario:
        """Validate and add scenario to queue.

        :param scenario_id: The scenario id to add to the queue
        :type scenario_id: str
        :raises NotFoundException: If scenario not found
        :raises BadRequestException: If scenario is already running or in queue
        :return: The scenario
        :rtype: Scenario
        """

        scenario = Scenario.get_by_id(scenario_id)
        if not scenario:
            raise NotFoundException(detail=f"Scenario '{scenario_id}' is not found")

        if Job.scenario_in_queue(scenario.id):
            raise BadRequestException("The scenario already is in the queue")

        # check scenario status
        if scenario.is_archived:
            raise BadRequestException("The scenario is archived, cannot add to queue")
        if scenario.is_validated:
            raise BadRequestException("The scenario is validated, cannot add to queue")
        if scenario.is_running:
            raise BadRequestException("The scenario is already running, cannot add to queue")
        if scenario.is_success:
            raise BadRequestException("The scenario is already finished, cannot add to queue")

        # reset the processes that are in error
        EntityNavigatorService.reset_error_processes_of_protocol(scenario.protocol_model)

        user = CurrentUserService.get_and_check_current_user()
        Job.add_job(user=user, scenario=scenario)

        # Try to run immediately instead of waiting for the next tick
        QueueRunner.try_run_next()

        return scenario

    @classmethod
    def remove_scenario_from_queue(cls, scenario_id: str) -> Scenario:
        """Remove scenario from queue and reset to DRAFT."""
        return Job.remove_scenario(scenario_id)

    @classmethod
    def get_queue_jobs(cls) -> list[Job]:
        """Get all jobs in queue."""
        return Job.get_all_jobs()

    @classmethod
    def scenario_is_in_queue(cls, scenario_id: str) -> bool:
        """Check if scenario is in queue."""
        return Job.scenario_in_queue(scenario_id)
