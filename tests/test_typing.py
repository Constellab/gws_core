# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

from gws_core import (BaseTestCase, ConfigParams, File, GTest, ProcessSpec,
                      Protocol, ProtocolService, ProtocolTyping,
                      ResourceTyping, RobotCreate, RobotEat, Sink, TaskService,
                      TaskTyping, protocol_decorator, transformer_decorator)
from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchDict
from gws_core.impl.robot.robot_protocol import RobotWorldTravelProto
from gws_core.impl.robot.robot_resource import Robot
from gws_core.model.typing import Typing
from gws_core.model.typing_service import TypingService
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.task.transformer.transformer import Transformer


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


@transformer_decorator(unique_name="TableTransformer", resource_type=File, human_name='My file transformer',
                       short_description="Anything is possible")
class FileTransformer(Transformer):
    pass


@transformer_decorator(unique_name="SubFileTransformer", resource_type=SubFile)
class SubFileTransformer(Transformer):
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
        self.assertTrue(len(world_travel_json['graph']['nodes']) > 0)
        self.assertTrue(len(world_travel_json['graph']['links']) > 0)

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
        typings: List[Typing] = TaskTyping.get_by_related_resource(SubFile, 'TRANSFORMER')

        # Check that we found the TableTransformer
        self.assertEqual(len([x for x in typings if x.model_name == 'TableTransformer']), 1)
        # Check that we found the SubFileTransformer
        self.assertEqual(len([x for x in typings if x.model_name == 'SubFileTransformer']), 1)

        # find task typings related to Table
        typings = TaskTyping.get_by_related_resource(File,  'TRANSFORMER')

        # Check that we found the TableTransformer
        self.assertEqual(len([x for x in typings if x.model_name == 'TableTransformer']), 1)
        # Check that the SubFileTransformer is not present
        self.assertEqual(len([x for x in typings if x.model_name == 'SubFileTransformer']), 0)

    async def test_get_typing(self):
        typing: Typing = TypingService.get_typing(SubFile._typing_name)
        self.assertIsInstance(typing, ResourceTyping)

        typing = TypingService.get_typing(FileTransformer._typing_name)
        self.assertIsInstance(typing, TaskTyping)

        typing = TypingService.get_typing(CreateSimpleRobot2._typing_name)
        self.assertIsInstance(typing, ProtocolTyping)

    async def test_typing_search(self):
        search_dict: SearchDict = SearchDict()

        # Search on name brick
        search_dict.filtersCriteria = [{'key': 'brick', "operator": "EQ", "value": "gws_core"}]
        paginator: Paginator[Typing] = TypingService.search(search_dict)
        self.assertTrue(paginator.page_info.number_of_items_per_page > 0)
        # Check that there is no Hide element
        self.assertEqual(len([x for x in paginator.current_items() if x.hide == True]), 0)

        # Search on full text
        search_dict.filtersCriteria = [{'key': 'text', "operator": "MATCH", "value": "file"}]
        paginator: Paginator[Typing] = TypingService.search(search_dict)
        # Test that it found the TableTransformer
        self.assertTrue(len([x for x in paginator.current_items() if x.model_name == 'TableTransformer']) > 0)

        search_dict.filtersCriteria = [{'key': 'text', "operator": "MATCH", "value": "possible is"}]
        paginator: Paginator[Typing] = TypingService.search(search_dict)
        # Test that it found the TableTransformer
        self.assertTrue(len([x for x in paginator.current_items() if x.model_name == 'TableTransformer']) > 0)

        search_dict.filtersCriteria = [{'key': 'text', "operator": "MATCH", "value": "TableTransformer"}]
        paginator: Paginator[Typing] = TypingService.search(search_dict)
        # Test that it found the TableTransformer
        self.assertTrue(len([x for x in paginator.current_items() if x.model_name == 'TableTransformer']) > 0)
