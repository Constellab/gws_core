# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

from gws_core import (BaseTestCase, ConfigParams, File, GTest, ProcessSpec,
                      Protocol, ProtocolService, ProtocolTyping,
                      ResourceTyping, RobotCreate, RobotEat, Sink, Task,
                      TaskService, TaskTyping, protocol_decorator,
                      transformer_decorator)
from gws_core.impl.robot.robot_protocol import RobotWorldTravelProto
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.table.table import Table
from gws_core.model.typing import Typing
from gws_core.resource.resource_decorator import resource_decorator


@protocol_decorator("CreateSimpleRobot2")
class CreateSimpleRobot2(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        facto: ProcessSpec = self.add_process(RobotCreate, 'facto')

        # define the protocol output
        sink_1: ProcessSpec = self.add_process(Sink, 'sink_1')

        self.add_connectors([
            (facto >> 'robot', sink_1 << 'resource'),
        ])


@resource_decorator('SubFile')
class SubFile(File):
    pass


@transformer_decorator(unique_name="TableTransformer", resource_type=File)
class FileTransformer(Task):
    pass


@transformer_decorator(unique_name="SubFileTransformer", resource_type=SubFile)
class SubFileTransformer(Task):
    pass


class TestTyping(BaseTestCase):

    async def test_typing(self):
        GTest.print("Model Typing")

        process_types = TaskService.get_task_typing_list().to_json()
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

    async def test_get_children_typings(self):
        typings: List[Typing] = Typing.get_children_typings('RESOURCE', File)

        # Check that we found the File type
        self.assertIsNotNone([x for x in typings if x.model_name == 'File'][0])
        # Check that we found the SubFile type
        self.assertIsNotNone([x for x in typings if x.model_name == 'SubFile'][0])

    async def test_get_by_related_resource(self):
        """Test the get of task typing by related resource
        """

        # find task typings related to Table
        typings: List[Typing] = TaskTyping.get_by_related_resource(SubFile)

        # Check that we found the TableTransformer
        self.assertEqual(len([x for x in typings if x.model_name == 'TableTransformer']), 1)
        # Check that we found the SubFileTransformer
        self.assertEqual(len([x for x in typings if x.model_name == 'SubFileTransformer']), 1)

        # find task typings related to Table
        typings = TaskTyping.get_by_related_resource(File)

        # Check that we found the TableTransformer
        self.assertEqual(len([x for x in typings if x.model_name == 'TableTransformer']), 1)
        # Check that the SubFileTransformer is not present
        self.assertEqual(len([x for x in typings if x.model_name == 'SubFileTransformer']), 0)
