# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import time

from gws_core import (ConfigParams, ProcessSpec, Protocol, RobotCreate,
                      RobotEat, RobotFood, RobotMove, RobotSugarCreate,
                      RobotWait, Task, TaskInputs, TaskOutputs,
                      protocol_decorator, task_decorator)

# File for Tests containing examples of protocols


@protocol_decorator("TestSimpleProtocol")
class TestSimpleProtocol(Protocol):
    def configure_protocol(self, params: ConfigParams) -> None:
        p0: ProcessSpec = self.add_process(RobotCreate, 'p0')
        p1: ProcessSpec = self.add_process(RobotMove, 'p1')
        p2: ProcessSpec = self.add_process(RobotEat, 'p2')
        p3: ProcessSpec = self.add_process(RobotMove, 'p3')
        p4: ProcessSpec = self.add_process(RobotMove, 'p4')
        p5: ProcessSpec = self.add_process(RobotEat, 'p5')
        p_wait: ProcessSpec = self.add_process(RobotWait, 'p_wait')

        self.add_connectors([
            (p0 >> 'robot', p1 << 'robot'),
            (p1 >> 'robot', p2 << 'robot'),
            (p2 >> 'robot', p_wait << 'robot'),
            (p_wait >> 'robot', p3 << 'robot'),
            (p3 >> 'robot', p4 << 'robot'),
            (p2 >> 'robot', p5 << 'robot')
        ])


@protocol_decorator("TestSubProtocol")
class TestSubProtocol(Protocol):
    def configure_protocol(self, params: ConfigParams) -> None:
        p1: ProcessSpec = self.add_process(RobotMove, 'p1')
        p2: ProcessSpec = self.add_process(RobotEat, 'p2')
        p3: ProcessSpec = self.add_process(RobotMove, 'p3')
        p4: ProcessSpec = self.add_process(RobotMove, 'p4')
        p_wait: ProcessSpec = self.add_process(RobotWait, 'p_wait')

        self.add_connectors([
            (p1 >> 'robot', p2 << 'robot'),
            (p2 >> 'robot', p_wait << 'robot'),
            (p_wait >> 'robot', p3 << 'robot'),
            (p2 >> 'robot', p4 << 'robot')
        ])

        self.add_interface('robot',  p1, 'robot'),
        self.add_outerface('robot',  p2, 'robot'),


@protocol_decorator("TestNestedProtocol")
class TestNestedProtocol(Protocol):
    def configure_protocol(self, params: ConfigParams) -> None:
        p0: ProcessSpec = self.add_process(RobotCreate, 'p0')
        p5: ProcessSpec = self.add_process(RobotEat, 'p5')
        mini_proto: ProcessSpec = self.add_process(TestSubProtocol, 'mini_proto')

        self.add_connectors([
            (p0 >> 'robot', mini_proto << 'robot'),
            (mini_proto >> 'robot', p5 << 'robot')
        ])


@task_decorator(unique_name="RobotWaitFood", human_name="Wait food",
                short_description="Wait food")
class RobotWaitFood(Task):
    """Wait 3
    """
    input_specs = {'food': RobotFood}
    output_specs = {'food': RobotFood}
    config_specs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        print("Wait food", flush=True)
        time.sleep(3)
        return {'food': inputs['food']}


@task_decorator(unique_name="RobotEmptyFood", human_name="Empty food",
                short_description="Empty food")
class RobotEmptyFood(Task):
    """Wait 3
    """
    input_specs = {}
    output_specs = {'food': RobotFood}
    config_specs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {}


@protocol_decorator("TestRobotWithSugarProtocol")
class TestRobotWithSugarProtocol(Protocol):
    """This test protocol test that the Eat task works with 2 entries.
    It also test that the eat task will wait for the Food input even if it is optional

    :param Protocol: [description]
    :type Protocol: [type]
    """

    def configure_protocol(self, params: ConfigParams) -> None:
        p0: ProcessSpec = self.add_process(RobotCreate, 'p0')
        sugar: ProcessSpec = self.add_process(RobotSugarCreate, 'sugar')
        wait_food: ProcessSpec = self.add_process(RobotWaitFood, 'wait_food')
        # Eat 1 need to wait for sugar and wait_food
        eat_1: ProcessSpec = self.add_process(RobotEat, 'eat_1').set_param('food_weight', 2)
        # Eat_2 is called even if the food input is not connected
        eat_2: ProcessSpec = self.add_process(RobotEat, 'eat_2').set_param('food_weight', 5)

        self.add_connectors([
            (p0 >> 'robot', eat_1 << 'robot'),
            (sugar >> 'sugar', wait_food << 'food'),
            (wait_food >> 'food', eat_1 << 'food'),
            (eat_1 >> 'robot', eat_2 << 'robot'),
        ])
