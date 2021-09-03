# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import time
from typing import Optional

from gws_core import (ConfigParams, Process, ProcessableSpec, process_decorator,
                      ProcessInputs, ProcessOutputs, Protocol,
                      protocol_decorator, RobotCreate, RobotEat, RobotFood,
                      RobotMove, RobotSugarCreate, RobotWait)

# File for Tests containing examples of protocols


@protocol_decorator("TestSimpleProtocol")
class TestSimpleProtocol(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        p0: ProcessableSpec = self.add_process(RobotCreate, 'p0')
        p1: ProcessableSpec = self.add_process(RobotMove, 'p1')
        p2: ProcessableSpec = self.add_process(RobotEat, 'p2')
        p3: ProcessableSpec = self.add_process(RobotMove, 'p3')
        p4: ProcessableSpec = self.add_process(RobotMove, 'p4')
        p5: ProcessableSpec = self.add_process(RobotEat, 'p5')
        p_wait: ProcessableSpec = self.add_process(RobotWait, 'p_wait')

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
    def configure_protocol(self, config_params: ConfigParams) -> None:
        p1: ProcessableSpec = self.add_process(RobotMove, 'p1')
        p2: ProcessableSpec = self.add_process(RobotEat, 'p2')
        p3: ProcessableSpec = self.add_process(RobotMove, 'p3')
        p4: ProcessableSpec = self.add_process(RobotMove, 'p4')
        p_wait: ProcessableSpec = self.add_process(RobotWait, 'p_wait')

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
    def configure_protocol(self, config_params: ConfigParams) -> None:
        p0: ProcessableSpec = self.add_process(RobotCreate, 'p0')
        p5: ProcessableSpec = self.add_process(RobotEat, 'p5')
        mini_proto: ProcessableSpec = self.add_process(TestSubProtocol, 'mini_proto')

        self.add_connectors([
            (p0 >> 'robot', mini_proto << 'robot'),
            (mini_proto >> 'robot', p5 << 'robot')
        ])


@process_decorator(unique_name="RobotWaitfood", human_name="Wait food",
                   short_description="Wait food")
class RobotWaitfood(Process):
    """Wait 3
    """
    input_specs = {'food': RobotFood}
    output_specs = {'food': RobotFood}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        print("Wait food", flush=True)
        time.sleep(3)
        return {'food': inputs['food']}


@process_decorator(unique_name="RobotEmptyfood", human_name="Empty food",
                   short_description="Empty food")
class RobotEmptyfood(Process):
    """Wait 3
    """
    input_specs = {}
    output_specs = {'food': Optional[RobotFood]}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        return {}


@protocol_decorator("TestRobotwithSugarProtocol")
class TestRobotwithSugarProtocol(Protocol):
    """This test protocol test that the Eat process works with 2 entries.
    It also test that the eat process will wait for the Food input even if it is optional

    :param Protocol: [description]
    :type Protocol: [type]
    """

    def configure_protocol(self, config_params: ConfigParams) -> None:
        p0: ProcessableSpec = self.add_process(RobotCreate, 'p0')
        sugar: ProcessableSpec = self.add_process(RobotSugarCreate, 'sugar')
        wait_food: ProcessableSpec = self.add_process(RobotWaitfood, 'wait_food')
        # Eat 1 need to wait for sugar and wait_food
        eat_1: ProcessableSpec = self.add_process(RobotEat, 'eat_1').configure('food_weight', 2)
        # Eat_2 is called even if the food input is not connected
        eat_2: ProcessableSpec = self.add_process(RobotEat, 'eat_2').configure('food_weight', 5)
        # Eat 3 is called event is the food input is connected but None
        empty_food: ProcessableSpec = self.add_process(RobotEmptyfood, 'empty_food')
        eat_3: ProcessableSpec = self.add_process(RobotEat, 'eat_3').configure('food_weight', 7)

        self.add_connectors([
            (p0 >> 'robot', eat_1 << 'robot'),
            (sugar >> 'sugar', wait_food << 'food'),
            (wait_food >> 'food', eat_1 << 'food'),
            (eat_1 >> 'robot', eat_2 << 'robot'),
            (empty_food >> 'food', eat_3 << 'food'),
            (eat_2 >> 'robot', eat_3 << 'robot'),
        ])
