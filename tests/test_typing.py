# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from gws_core import (BaseTestCase, ConfigParams, GTest, ProcessSpec, Protocol,
                      ProtocolService, ProtocolTyping, ResourceTyping,
                      RobotCreate, RobotEat, Sink, TaskService, TaskTyping,
                      protocol_decorator)
from gws_core.impl.robot.robot_protocol import RobotWorldTravelProto
from gws_core.impl.robot.robot_resource import Robot


@protocol_decorator("CreateSimpleRobot2")
class CreateSimpleRobot2(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        facto: ProcessSpec = self.add_process(RobotCreate, 'facto')

        # define the protocol output
        sink_1: ProcessSpec = self.add_process(Sink, 'sink_1')

        self.add_connectors([
            (facto >> 'robot', sink_1 << 'resource'),
        ])


class TestTyping(BaseTestCase):

    async def test_typing(self):
        GTest.print("Model Typing")

        process_types = TaskService.fetch_task_typing_list().to_json()
        self.assertTrue(len(process_types["objects"]) > 0)

        protocol_types = ProtocolService.fetch_protocol_type_list().to_json()
        self.assertTrue(len(protocol_types["objects"]) > 0)

    async def test_process_type(self):
        """Test a get from a type and test convertion to json of a type that
        has mulitple spec and an optional spec
        """
        eat_type: TaskTyping = TaskTyping.get_by_model_type(RobotEat)

        self.assertEqual(eat_type.get_type(), RobotEat)

        eat_json: Dict = eat_type.to_json(deep=True)

        self.assertEqual(eat_json['typing_name'], 'TASK.gws_core.RobotEat')
        self.assertIsNotNone(eat_json['input_specs'])
        self.assertIsNotNone(eat_json['input_specs']['robot'])
        self.assertIsNotNone(eat_json['input_specs']['food'])

    async def test_protocol_type(self):
        world_travel: ProtocolTyping = ProtocolTyping.get_by_model_type(RobotWorldTravelProto)

        self.assertEqual(world_travel.get_type(), RobotWorldTravelProto)

        world_travel_json: Dict = world_travel.to_json(deep=True)

        self.assertEqual(world_travel_json['typing_name'], 'PROTOCOL.gws_core.RobotWorldTravelProto')
        self.assertTrue(len(world_travel_json['data']['graph']['nodes']) > 0)
        self.assertTrue(len(world_travel_json['data']['graph']['links']) > 0)

    async def test_resource_type(self):
        robot: ResourceTyping = ResourceTyping.get_by_model_type(Robot)

        self.assertEqual(robot.get_type(), Robot)

        robot_json: Dict = robot.to_json(deep=True)

        self.assertEqual(robot_json['typing_name'], 'RESOURCE.gws_core.Robot')
