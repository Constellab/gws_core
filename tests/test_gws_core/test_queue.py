import time

from gws_core import BaseTestCase, Job, QueueRunner, QueueService, Scenario, ScenarioService, ScenarioStatus
from gws_core.impl.robot.robot_protocol import RobotSimpleTravel
from gws_core.impl.robot.robot_service import RobotService
from gws_core.test.test_helper import TestHelper


# test_queue
class TestQueue(BaseTestCase):
    def test_queue(self):
        self.assertEqual(Scenario.count_running_or_queued_scenarios(), 0)
        self.assertEqual(Job.queue_length(), 0)

        proto1 = RobotService.create_robot_world_travel()
        scenario1: Scenario = ScenarioService.create_scenario_from_protocol_model(
            protocol_model=proto1
        )
        Job.add_job(user=TestHelper.user, scenario=scenario1)

        scenario1 = scenario1.refresh()
        self.assertEqual(scenario1.status, ScenarioStatus.IN_QUEUE)

        self.assertEqual(Job.queue_length(), 1)
        job1 = Job.pop_first()
        self.assertEqual(Job.queue_length(), 0)
        self.assertEqual(scenario1.id, job1.scenario.id)

        Job.add_job(user=TestHelper.user, scenario=scenario1)
        self.assertEqual(Job.queue_length(), 1)
        Job.remove_scenario(scenario1.id)
        self.assertEqual(Job.queue_length(), 0)

        scenario1 = scenario1.refresh()
        self.assertEqual(scenario1.status, ScenarioStatus.DRAFT)

    def test_queue_run(self):
        # init the ticking, tick each second
        QueueRunner.init(tick_interval=3, daemon=True)

        scenario2: Scenario = ScenarioService.create_scenario_from_protocol_type(RobotSimpleTravel)

        scenario3: Scenario = ScenarioService.create_scenario_from_protocol_type(RobotSimpleTravel)

        Job.add_job(user=TestHelper.user, scenario=scenario2)
        Job.add_job(user=TestHelper.user, scenario=scenario3)

        self.assertEqual(Job.queue_length(), 2)
        self._wait_for_scenarios()
        self.assertEqual(Job.queue_length(), 0)

        scenario2 = scenario2.refresh()
        scenario3 = scenario3.refresh()
        self.assertEqual(scenario2.status, ScenarioStatus.SUCCESS)
        self.assertEqual(scenario3.status, ScenarioStatus.SUCCESS)

        # Stop the tick loop to prevent background threads from querying dropped tables
        QueueRunner.deinit()

    def test_add_job_without_queue_runner(self):
        """Test that adding a job via QueueService writes to DB without triggering execution."""
        scenario: Scenario = ScenarioService.create_scenario_from_protocol_type(RobotSimpleTravel)

        Job.add_job(user=TestHelper.user, scenario=scenario)

        # The job should be in the queue DB
        self.assertEqual(Job.queue_length(), 1)
        self.assertTrue(QueueService.scenario_is_in_queue(scenario.id))

        # The scenario should be marked as in queue, not running or success
        scenario = scenario.refresh()
        self.assertEqual(scenario.status, ScenarioStatus.IN_QUEUE)

        # Clean up
        Job.remove_scenario(scenario.id)

    def _wait_for_scenarios(self) -> None:
        wait_count = 0
        # Wait until the queue is clear and there is not scenario that is running
        while Job.queue_length() > 0 or Scenario.count_running_or_queued_scenarios() > 0:
            print("Waiting 5 secs for cli scenarios to finish ...")
            time.sleep(5)
            if wait_count >= 10:
                raise Exception("The scenario queue is not empty")
            wait_count += 1
