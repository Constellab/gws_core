
from gws_core import BaseTestCase
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.core.model.model import Model
from gws_core.entity_action.entity_action import EntityAction
from gws_core.entity_action.entity_action_dto import (
    EntityActionButtonDTO,
    EntityActionResultDTO,
)
from gws_core.entity_action.entity_action_plugin import EntityActionPlugin
from gws_core.entity_action.entity_action_registry import EntityActionRegistry
from gws_core.entity_action.entity_action_service import EntityActionService
from gws_core.entity_action.entity_action_type import EntityActionType
from gws_core.impl.robot.robot_resource import Robot
from gws_core.note.note import Note
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel

# A dummy plugin registered manually inside the test (not via the decorator) so
# the test does not pollute the global registry of the running app.
# plugin_id mimics what the decorator builds: '<brick_name>.<plugin_name>'.
_DUMMY_PLUGIN_ID = "gws_core.test_dummy_resource"


class _DummyResourcePlugin(EntityActionPlugin):
    entity_action_type = EntityActionType.RESOURCE
    __plugin_name__ = "test_dummy_resource"
    __plugin_id__ = _DUMMY_PLUGIN_ID

    def get_actions(self, entity: Model) -> list[EntityAction]:
        return [EntityAction.button(action_name="do_something", text="Do something",
                                    icon="bolt")]

    def execute_action(self, entity: Model, action_name: str) -> EntityActionResultDTO:
        if action_name != "do_something":
            raise Exception(f"Unknown action '{action_name}'")
        return EntityActionResultDTO(navigate_to="/somewhere",
                                     navigate_query_params={"id": entity.id})


# test_entity_action
class TestEntityAction(BaseTestCase):

    def setUp(self) -> None:
        super().setUp()
        EntityActionRegistry.register(_DummyResourcePlugin)

    def tearDown(self) -> None:
        # remove the dummy plugin so other tests are not affected
        EntityActionRegistry._plugins.get(EntityActionType.RESOURCE, {}).pop(
            _DUMMY_PLUGIN_ID, None
        )
        super().tearDown()

    def test_entity_type_model_mapping(self):
        self.assertEqual(EntityActionType.RESOURCE.get_entity_model_type(),
                         ResourceModel)
        self.assertEqual(EntityActionType.NOTE.get_entity_model_type(), Note)

    def test_namespacing(self):
        action = EntityAction.button(action_name="do_something", text="Do something")
        dto = action.to_dto("my_brick.my_plugin")
        self.assertIsInstance(dto, EntityActionButtonDTO)
        self.assertEqual(dto.action_name, "my_brick.my_plugin.do_something")

    def test_get_actions(self):
        resource_model = ResourceModel.save_from_resource(
            Robot.empty(), origin=ResourceOrigin.UPLOADED
        )

        # the dummy plugin returns one action for resources
        actions = EntityActionService.get_entity_actions(
            EntityActionType.RESOURCE, resource_model.id
        )
        self.assertEqual(len(actions), 1)
        self.assertIsInstance(actions[0], EntityActionButtonDTO)
        self.assertEqual(actions[0].action_name,
                         f"{_DUMMY_PLUGIN_ID}.do_something")

        # no plugin registered for notes -> empty menu (type isolation)
        note = Note()
        note.title = "test note"
        note.save()
        note_actions = EntityActionService.get_entity_actions(
            EntityActionType.NOTE, note.id
        )
        self.assertEqual(note_actions, [])

    def test_execute_action(self):
        resource_model = ResourceModel.save_from_resource(
            Robot.empty(), origin=ResourceOrigin.UPLOADED
        )

        result = EntityActionService.execute_entity_action(
            EntityActionType.RESOURCE, resource_model.id,
            f"{_DUMMY_PLUGIN_ID}.do_something"
        )
        self.assertEqual(result.navigate_to, "/somewhere")
        self.assertEqual(result.navigate_query_params, {"id": resource_model.id})

        # unknown plugin -> BadRequestException
        with self.assertRaises(BadRequestException):
            EntityActionService.execute_entity_action(
                EntityActionType.RESOURCE, resource_model.id,
                "some_brick.unknown_plugin.do_something"
            )

        # action name without namespace -> BadRequestException
        with self.assertRaises(BadRequestException):
            EntityActionService.execute_entity_action(
                EntityActionType.RESOURCE, resource_model.id, "no_namespace"
            )

    def test_duplicate_registration_raises(self):
        # registering a second plugin with the same plugin_id must raise,
        # the dummy plugin is already registered in setUp
        with self.assertRaisesRegex(Exception, "same id"):
            EntityActionRegistry.register(_DummyResourcePlugin)
