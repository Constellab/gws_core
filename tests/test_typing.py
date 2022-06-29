# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

from gws_core import (BaseTestCase, File, ProcessSpec, Protocol,
                      ProtocolTyping, ResourceTyping, RobotCreate, RobotEat,
                      Sink, TaskTyping, protocol_decorator,
                      transformer_decorator)
from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.impl.robot.robot_protocol import RobotTravelProto
from gws_core.impl.robot.robot_resource import Robot
from gws_core.model.typing import Typing
from gws_core.model.typing_service import TypingService
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.task.transformer.transformer import Transformer


@protocol_decorator("CreateSimpleRobot2")
class CreateSimpleRobot2(Protocol):
    def configure_protocol(self) -> None:
        facto: ProcessSpec = self.add_process(RobotCreate, 'facto')

        # define the protocol output
        sink_1: ProcessSpec = self.add_process(Sink, 'sink_1')

        self.add_connectors([
            (facto >> 'robot', sink_1 << 'resource'),
        ])


@protocol_decorator("CreateSimpleRobot2Deprecated", deprecated_since="0.3.10",
                    deprecated_message="Use CreateSimpleRobot2")
class CreateSimpleRobot2Deprecated(Protocol):
    pass


@resource_decorator('SubFile')
class SubFile(File):
    pass


@transformer_decorator(unique_name="FileTransformer", resource_type=File, human_name='My file transformer',
                       short_description="Anything is possible")
class FileTransformer(Transformer):
    pass


@transformer_decorator(unique_name="SubFileTransformer", resource_type=SubFile)
class SubFileTransformer(Transformer):
    pass


class TestTyping(BaseTestCase):

    async def test_process_type(self):
        """Test a get from a type and test convertion to json of a type that
        has mulitple spec and an optional spec
        """
        eat_type: TaskTyping = TaskTyping.get_by_model_type(RobotEat)

        self.assertEqual(eat_type.get_type(), RobotEat)

        eat_json: Dict = eat_type.to_json(deep=True)

        self.assertIsNotNone(eat_json['input_specs'])
        self.assertIsNotNone(eat_json['input_specs']['robot'])
        self.assertIsNotNone(eat_json['input_specs']['food'])

    async def test_protocol_type(self):
        world_travel: ProtocolTyping = ProtocolTyping.get_by_model_type(RobotTravelProto)

        self.assertEqual(world_travel.get_type(), RobotTravelProto)

        world_travel_json: Dict = world_travel.to_json(deep=True)

        self.assertIsNotNone(world_travel_json['input_specs']['robot'])
        self.assertIsNotNone(world_travel_json['output_specs']['robot'])

    async def test_resource_type(self):
        robot: ResourceTyping = ResourceTyping.get_by_model_type(Robot)

        self.assertEqual(robot.get_type(), Robot)

        robot_json: Dict = robot.to_json(deep=True)

        self.assertEqual(robot_json['typing_name'], 'RESOURCE.gws_core.Robot')

    async def test_get_children_typings(self):
        typings: List[Typing] = Typing.get_children_typings('RESOURCE', File)

        # Check that we found the File type
        self.assertIsNotNone([x for x in typings if x.unique_name == 'File'][0])
        # Check that we found the SubFile type
        self.assertIsNotNone([x for x in typings if x.unique_name == 'SubFile'][0])

    async def test_get_by_related_resource(self):
        """Test the get of task typing by related resource
        """

        # find task typings related to Table
        typings: List[Typing] = TaskTyping.get_by_related_resource(SubFile, 'TRANSFORMER')

        # Check that we found the FileTransformer
        self.assertEqual(len([x for x in typings if x.unique_name == 'FileTransformer']), 1)
        # Check that we found the SubFileTransformer
        self.assertEqual(len([x for x in typings if x.unique_name == 'SubFileTransformer']), 1)

        # find task typings related to Table
        typings = TaskTyping.get_by_related_resource(File,  'TRANSFORMER')

        # Check that we found the FileTransformer
        self.assertEqual(len([x for x in typings if x.unique_name == 'FileTransformer']), 1)
        # Check that the SubFileTransformer is not present
        self.assertEqual(len([x for x in typings if x.unique_name == 'SubFileTransformer']), 0)

    async def test_get_typing(self):
        typing: Typing = TypingService.get_typing(SubFile._typing_name)
        self.assertIsInstance(typing, ResourceTyping)

        typing = TypingService.get_typing(FileTransformer._typing_name)
        self.assertIsInstance(typing, TaskTyping)

        typing = TypingService.get_typing(CreateSimpleRobot2._typing_name)
        self.assertIsInstance(typing, ProtocolTyping)

    async def test_typing_search(self):
        search_dict: SearchParams = SearchParams()

        # Search on name brick
        search_dict.filtersCriteria = [{'key': 'brick', "operator": "EQ", "value": "gws_core"}]
        paginator: Paginator[Typing] = TypingService.search(search_dict)
        self.assertTrue(paginator.page_info.number_of_items_per_page > 0)
        # Check that there is no Hide element
        self.assertEqual(len([x for x in paginator.results if x.hide == True]), 0)

        # Search on full text
        search_dict.filtersCriteria = [{'key': 'text', "operator": "MATCH", "value": "file"}]
        paginator: Paginator[Typing] = TypingService.search(search_dict)
        # Test that it found the FileTransformer
        self.assertTrue(len([x for x in paginator.results if x.unique_name == 'FileTransformer']) > 0)

        search_dict.filtersCriteria = [{'key': 'text', "operator": "MATCH", "value": "possible is"}]
        paginator: Paginator[Typing] = TypingService.search(search_dict)
        # Test that it found the FileTransformer
        self.assertTrue(len([x for x in paginator.results if x.unique_name == 'FileTransformer']) > 0)

        search_dict.filtersCriteria = [{'key': 'text', "operator": "MATCH", "value": "FileTransformer"}]
        paginator: Paginator[Typing] = TypingService.search(search_dict)
        # Test that it found the FileTransformer
        self.assertTrue(len([x for x in paginator.results if x.unique_name == 'FileTransformer']) > 0)

        # # Test search on related model
        paginator: Paginator[Typing] = TypingService.search_transformers([SubFile._typing_name], SearchParams())
        # Test that it found the FileTransformer
        self.assertTrue(len([x for x in paginator.results if x.unique_name == 'FileTransformer']) > 0)

    async def test_typing_search_with_deprecated(self):
        search_dict: SearchParams = SearchParams()

        # Test with deprecated typing, it should not be found
        search_dict.filtersCriteria = [{'key': 'text', "operator": "MATCH", "value": "CreateSimpleRobot2Deprecated"},
                                       {'key': 'include_deprecated', "operator": "EQ", "value": False}]
        paginator: Paginator[Typing] = TypingService.search(search_dict)
        # Test that it found the FileTransformer
        self.assertEqual(paginator.page_info.total_number_of_items, 0)

        # Test with deprecated typing and found option, it should be found
        search_dict.filtersCriteria = [{'key': 'text', "operator": "MATCH", "value": "CreateSimpleRobot2Deprecated"},
                                       {'key': 'include_deprecated', "operator": "EQ", "value": True}]
        paginator: Paginator[Typing] = TypingService.search(search_dict)
        # Test that it found the FileTransformer
        self.assertTrue(len([x for x in paginator.results
                        if x.unique_name == 'CreateSimpleRobot2Deprecated']) > 0)
