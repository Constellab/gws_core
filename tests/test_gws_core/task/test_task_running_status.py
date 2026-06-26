from typing import cast

from gws_core import (
    BaseTestCase,
    ConfigParams,
    Protocol,
    ProtocolModel,
    Scenario,
    ScenarioService,
    Task,
    TaskInputs,
    TaskModel,
    TaskOutputs,
    protocol_decorator,
    task_decorator,
)
from gws_core.process.process_types import ProcessStatus
from gws_core.scenario.scenario_run_service import ScenarioRunService

# Holds the status of the task model, as persisted in the database, observed
# from inside the task's run method (i.e. while the task is running). The
# scenario is run in-process (ScenarioRunService.run_scenario) so this module
# global is shared between the task run and the assertion.
_STATUS_DURING_RUN: dict[str, ProcessStatus | None] = {"status": None}


@task_decorator(unique_name="CheckRunningStatusTask")
class CheckRunningStatusTask(Task):
    """Task that, while running, reloads its own TaskModel from the database and
    records the persisted status. While the task is running the status must be
    RUNNING.
    """

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        scenario_id = self.get_scenario_id()

        # Reload the task model from the database (fresh read), to get the status
        # as it was persisted by mark_as_started just before the run started.
        task_model = cast(
            TaskModel,
            TaskModel.select().where(TaskModel.scenario == scenario_id).first(),
        )

        _STATUS_DURING_RUN["status"] = task_model.status if task_model else None
        return {}


@protocol_decorator(unique_name="CheckRunningStatusProtocol")
class CheckRunningStatusProtocol(Protocol):
    def configure_protocol(self) -> None:
        self.add_process(CheckRunningStatusTask, "check_running")


# test_task_running_status
class TestTaskRunningStatus(BaseTestCase):
    def test_task_marked_as_running_during_run(self):
        """A task that is being run by a scenario must be marked as RUNNING in
        the database while its run method executes (it must not stay DRAFT and
        jump straight to SUCCESS).
        """
        _STATUS_DURING_RUN["status"] = None

        # Run the scenario in-process (not in a subprocess) so the task run and
        # this test share the same module global.
        scenario: Scenario = ScenarioService.create_scenario_from_protocol_type(
            CheckRunningStatusProtocol
        )
        ScenarioRunService.run_scenario(scenario=scenario)

        # sanity check: the task did run and the observer captured a value
        protocol: ProtocolModel = scenario.protocol_model
        task: TaskModel = cast(TaskModel, protocol.get_process("check_running"))
        self.assertTrue(task.is_success)

        self.assertEqual(
            _STATUS_DURING_RUN["status"],
            ProcessStatus.RUNNING,
            "The task must be marked as RUNNING in the database while it is running, "
            f"but its persisted status was '{_STATUS_DURING_RUN['status']}'.",
        )
