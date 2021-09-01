# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from gws_core import GTest, ProcessService, ProtocolService, RobotEat
from gws_core.impl.robot.robot_protocol import RobotWorldTravelProto
from gws_core.impl.robot.robot_resource import Robot
from gws_core.process.process_type import ProcessType
from gws_core.protocol.protocol_type import ProtocolType
from gws_core.resource.resource_type import ResourceType

from tests.base_test import BaseTest


class TestTyping(BaseTest):

    async def test_typing(self):
        GTest.print("Model Typing")

        process_types = ProcessService.fetch_process_type_list().to_json()
        self.assertTrue(len(process_types["objects"]) > 0)

        protocol_types = ProtocolService.fetch_protocol_type_list().to_json()
        self.assertTrue(len(protocol_types["objects"]) > 0)

    async def test_process_type(self):
        """Test a get from a type and test convertion to json of a type that
        has mulitple spec and an optional spec
        """
        eat_type: ProcessType = ProcessType.get_by_model_type(RobotEat)

        self.assertEqual(eat_type.get_type(), RobotEat)

        eat_json: Dict = eat_type.to_json(deep=True)

        input_specs: Dict = {'robot': ['RESOURCE.gws_core.Robot'], 'food': ['RESOURCE.gws_core.RobotFood', None]}
        self.assertEqual(eat_json['typing_name'], 'PROCESS.gws_core.RobotEat')
        self.assert_json(eat_json['input_specs'], input_specs, None)

    async def test_protocol_type(self):
        world_travel: ProtocolType = ProtocolType.get_by_model_type(RobotWorldTravelProto)

        self.assertEqual(world_travel.get_type(), RobotWorldTravelProto)

        world_travel_json: Dict = world_travel.to_json(deep=True)

        self.assertEqual(world_travel_json['typing_name'], 'PROTOCOL.gws_core.RobotWorldTravelProto')
        self.assertTrue(len(world_travel_json['data']['graph']['nodes']) > 0)
        self.assertTrue(len(world_travel_json['data']['graph']['links']) > 0)

    async def test_resource_type(self):
        robot: ResourceType = ResourceType.get_by_model_type(Robot)

        self.assertEqual(robot.get_type(), Robot)

        robot_json: Dict = robot.to_json(deep=True)

        self.assertEqual(robot_json['typing_name'], 'RESOURCE.gws_core.Robot')
