

import time

from gws_core import (BaseTestCase, Queue, QueueService, Scenario,
                      ScenarioService, ScenarioStatus)
from gws_core.impl.robot.robot_protocol import RobotSimpleTravel
from gws_core.impl.robot.robot_service import RobotService
from gws_core.test.test_helper import TestHelper


# test_queue
class TestQueue(BaseTestCase):

    def test_queue(self):

        queue: Queue = Queue().save()
        self.assertEqual(Scenario.count_running_or_queued_scenarios(), 0)
        self.assertEqual(queue.length(), 0)

        proto1 = RobotService.create_robot_world_travel()
        scenario1: Scenario = ScenarioService.create_scenario_from_protocol_model(
            protocol_model=proto1)
        Queue.add_job(user=TestHelper.user, scenario=scenario1)

        scenario1 = scenario1.refresh()
        self.assertEqual(scenario1.status, ScenarioStatus.IN_QUEUE)

        self.assertEqual(Queue.length(), 1)
        job1 = queue.pop_first()
        self.assertEqual(Queue.length(), 0)
        self.assertEqual(scenario1.id, job1.scenario.id)

        Queue.add_job(user=TestHelper.user, scenario=scenario1)
        self.assertEqual(Queue.length(), 1)
        Queue.remove_scenario(scenario1.id)
        self.assertEqual(Queue.length(), 0)

        scenario1 = scenario1.refresh()
        self.assertEqual(scenario1.status, ScenarioStatus.DRAFT)

    def test_queue_run(self):
        # init the ticking, tick each second
        QueueService.init(tick_interval=3)

        scenario2: Scenario = ScenarioService.create_scenario_from_protocol_type(
            RobotSimpleTravel)

        scenario3: Scenario = ScenarioService.create_scenario_from_protocol_type(
            RobotSimpleTravel)

        QueueService._add_job(user=TestHelper.user, scenario=scenario2)
        QueueService._add_job(user=TestHelper.user, scenario=scenario3)

        self.assertEqual(Queue.length(), 2)
        self._wait_for_scenarios()
        self.assertEqual(Queue.length(), 0)

        scenario2 = scenario2.refresh()
        scenario3 = scenario3.refresh()
        self.assertEqual(scenario2.status, ScenarioStatus.SUCCESS)
        self.assertEqual(scenario3.status, ScenarioStatus.SUCCESS)

    def _wait_for_scenarios(self) -> None:

        wait_count = 0
        # Wait until the queue is clear and there is not scenario that is running
        while Queue.length() > 0 or Scenario.count_running_or_queued_scenarios() > 0:
            print("Waiting 5 secs for cli scenarios to finish ...")
            time.sleep(5)
            if wait_count >= 10:
                raise Exception("The scenario queue is not empty")
            wait_count += 1
