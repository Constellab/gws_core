
from gws_core import (
    BaseTestCase,
    File,
    OutputTask,
    ProcessSpec,
    Protocol,
    ProtocolTyping,
    ResourceTyping,
    TaskTyping,
    protocol_decorator,
    transformer_decorator,
)
from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchFilterCriteria, SearchOperator, SearchParams
from gws_core.impl.robot.robot_protocol import RobotTravelProto
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotEat
from gws_core.model.typing import Typing
from gws_core.model.typing_deprecated import TypingDeprecated
from gws_core.model.typing_service import TypingService
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.task.transformer.transformer import Transformer


@protocol_decorator("CreateSimpleRobot2")
class CreateSimpleRobot2(Protocol):
    def configure_protocol(self) -> None:
        facto: ProcessSpec = self.add_process(RobotCreate, "facto")

        # define the protocol output
        output_1: ProcessSpec = self.add_process(OutputTask, "output_1")

        self.add_connectors(
            [
                (facto >> "robot", output_1 << "resource"),
            ]
        )


@protocol_decorator(
    "CreateSimpleRobot2Deprecated",
    deprecated=TypingDeprecated(
        deprecated_since="0.3.10", deprecated_message="Use CreateSimpleRobot2"
    ),
)
class CreateSimpleRobot2Deprecated(Protocol):
    pass


@resource_decorator("SubFileTyping")
class SubFileTyping(File):
    pass


@transformer_decorator(
    unique_name="FileTransformer",
    resource_type=File,
    human_name="My file transformer",
    short_description="Anything is possible",
)
class FileTransformer(Transformer):
    pass


@transformer_decorator(unique_name="SubFileTransformer", resource_type=SubFileTyping)
class SubFileTransformer(Transformer):
    pass


# test_typing
class TestTyping(BaseTestCase):
    def test_process_type(self):
        """Test a get from a type and test convertion to json of a type that
        has mulitple spec and an optional spec
        """
        eat_type: TaskTyping = TaskTyping.get_by_model_type(RobotEat)

        self.assertEqual(eat_type.get_type(), RobotEat)

        eat_json = eat_type.to_full_dto()

        self.assertIsNotNone(eat_json.input_specs)
        self.assertIsNotNone(eat_json.input_specs.specs)
        self.assertIsNotNone(eat_json.input_specs.specs["robot"])
        self.assertIsNotNone(eat_json.input_specs.specs["food"])

    def test_protocol_type(self):
        world_travel: ProtocolTyping = ProtocolTyping.get_by_model_type(RobotTravelProto)

        self.assertEqual(world_travel.get_type(), RobotTravelProto)

        world_travel_json = world_travel.to_full_dto()

        self.assertIsNotNone(world_travel_json.input_specs.specs["travel_int"])
        self.assertIsNotNone(world_travel_json.output_specs.specs["travel_out"])

    def test_resource_type(self):
        robot: ResourceTyping = ResourceTyping.get_by_model_type(Robot)

        self.assertEqual(robot.get_type(), Robot)

        robot_json = robot.to_full_dto()

        self.assertEqual(robot_json.typing_name, "RESOURCE.gws_core.Robot")

    def test_get_children_typings(self):
        typings: list[Typing] = Typing.get_children_typings("RESOURCE", File)

        # Check that we found the File type
        self.assertIsNotNone([x for x in typings if x.unique_name == "File"][0])
        # Check that we found the SubFileTyping type
        self.assertIsNotNone([x for x in typings if x.unique_name == "SubFileTyping"][0])

    def test_get_by_related_resource(self):
        """Test the get of task typing by related resource"""

        # find task typings related to Table
        typings: list[Typing] = TaskTyping.get_by_related_resource(SubFileTyping, "TRANSFORMER")

        # Check that we found the FileTransformer
        self.assertEqual(len([x for x in typings if x.unique_name == "FileTransformer"]), 1)
        # Check that we found the SubFileTransformer
        self.assertEqual(len([x for x in typings if x.unique_name == "SubFileTransformer"]), 1)

        # find task typings related to Table
        typings = TaskTyping.get_by_related_resource(File, "TRANSFORMER")

        # Check that we found the FileTransformer
        self.assertEqual(len([x for x in typings if x.unique_name == "FileTransformer"]), 1)
        # Check that the SubFileTransformer is not present
        self.assertEqual(len([x for x in typings if x.unique_name == "SubFileTransformer"]), 0)

    def test_get_typing(self):
        typing: Typing = TypingService.get_and_check_typing(SubFileTyping.get_typing_name())
        self.assertIsInstance(typing, ResourceTyping)

        typing = TypingService.get_and_check_typing(FileTransformer.get_typing_name())
        self.assertIsInstance(typing, TaskTyping)

        typing = TypingService.get_and_check_typing(CreateSimpleRobot2.get_typing_name())
        self.assertIsInstance(typing, ProtocolTyping)

    def test_typing_search(self):
        search_params: SearchParams = SearchParams()

        # Search on name brick
        search_params.set_filters_criteria(
            [SearchFilterCriteria(key="brick", operator=SearchOperator.EQ, value="gws_core")]
        )
        paginator: Paginator[Typing] = TypingService.search(search_params)
        self.assertTrue(paginator.page_info.number_of_items_per_page > 0)
        # Check that there is no Hide element
        self.assertEqual(len([x for x in paginator.results if x.hide == True]), 0)

        # Search on text
        search_params.set_filters_criteria(
            [SearchFilterCriteria(key="text", operator=SearchOperator.CONTAINS, value="filetra")]
        )
        paginator = TypingService.search(search_params)
        # Test that it found the FileTransformer
        self.assertTrue(
            len([x for x in paginator.results if x.unique_name == "FileTransformer"]) > 0
        )

        search_params.set_filters_criteria(
            [SearchFilterCriteria(key="text", operator=SearchOperator.CONTAINS, value="possib")]
        )
        paginator = TypingService.search(search_params)
        # Test that it found the FileTransformer
        self.assertTrue(
            len([x for x in paginator.results if x.unique_name == "FileTransformer"]) > 0
        )

        search_params.set_filters_criteria(
            [
                SearchFilterCriteria(
                    key="text", operator=SearchOperator.CONTAINS, value="FileTransformer"
                )
            ]
        )
        paginator = TypingService.search(search_params)
        # Test that it found the FileTransformer
        self.assertTrue(
            len([x for x in paginator.results if x.unique_name == "FileTransformer"]) > 0
        )

        # # Test search on related model
        paginator = TypingService.search_transformers(
            [SubFileTyping.get_typing_name()], SearchParams()
        )
        # Test that it found the FileTransformer
        self.assertTrue(
            len([x for x in paginator.results if x.unique_name == "FileTransformer"]) > 0
        )

    def test_typing_search_with_deprecated(self):
        search_dict: SearchParams = SearchParams()

        # Test with deprecated typing, it should not be found
        search_dict.set_filters_criteria(
            [
                SearchFilterCriteria(
                    key="text", operator=SearchOperator.MATCH, value="CreateSimpleRobot2Deprecated"
                ),
                SearchFilterCriteria(
                    key="include_deprecated", operator=SearchOperator.EQ, value=False
                ),
            ]
        )
        paginator: Paginator[Typing] = TypingService.search(search_dict)
        # Test that it found the FileTransformer
        self.assertEqual(paginator.page_info.total_number_of_items, 0)

        # Test with deprecated typing and found option, it should be found
        search_dict.set_filters_criteria(
            [
                SearchFilterCriteria(
                    key="text", operator=SearchOperator.MATCH, value="CreateSimpleRobot2Deprecated"
                ),
                SearchFilterCriteria(
                    key="include_deprecated", operator=SearchOperator.EQ, value=True
                ),
            ]
        )
        paginator = TypingService.search(search_dict)
        # Test that it found the FileTransformer
        self.assertTrue(
            len([x for x in paginator.results if x.unique_name == "CreateSimpleRobot2Deprecated"])
            > 0
        )

    def test_typing_search_by_name(self):
        typings: list[Typing] = list(
            Typing.get_by_object_type_and_name("PROTOCOL", "SimpleRobot2Deprecated")
        )
        self.assertEqual(len(typings), 1)
        self.assertEqual(typings[0].unique_name, "CreateSimpleRobot2Deprecated")
