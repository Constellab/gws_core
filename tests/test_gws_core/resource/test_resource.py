
from gws_core import BaseTestCase, File, IntRField, ListRField, ResourceModel, StrRField
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate
from gws_core.process.process_proxy import ProcessProxy
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.technical_info import TechnicalInfo
from gws_core.scenario.scenario_proxy import ScenarioProxy


@resource_decorator(unique_name="TestResourceFields")
class TestResourceFields(Resource):
    age: int = IntRField()
    position: list[float] = ListRField()

    long_str = StrRField()


@resource_decorator(unique_name="TestResourceFieldsFile")
class TestResourceFieldsFile(File):
    age: int = IntRField()
    position: list[float] = ListRField()

    long_str = StrRField()


# test_resource
class TestResource(BaseTestCase):
    def test_resource(self):
        i_scenario = ScenarioProxy()
        i_scenario.get_protocol().add_process(RobotCreate, instance_name="create")
        i_scenario.run()

        create: ProcessProxy = i_scenario.get_protocol().get_process("create")

        # Check that the resource model was generated
        resource_model: ResourceModel = create.get_output_resource_model("robot")
        self.assertIsNotNone(resource_model.id)
        self.assertTrue(isinstance(resource_model, ResourceModel))
        self.assertEqual(resource_model.origin, ResourceOrigin.GENERATED)
        self.assertEqual(resource_model.generated_by_port_name, "robot")

        # Check that the resource is a Robot
        robot: Robot = resource_model.get_resource()
        self.assertTrue(isinstance(robot, Robot))

        # Check the to_json
        resource_model.to_dto()

    def test_resource_r_fields(self):
        """Test that RField are loaded and long field are lazy loaded"""
        resource = TestResourceFields()
        resource.position = [5, 2]
        resource.age = 12
        resource.long_str = "Hello world"

        resource_model: ResourceModel = ResourceModel.from_resource(
            resource, origin=ResourceOrigin.UPLOADED
        )

        self.assertEqual(len(resource_model.data), 2)
        self.assertIsNotNone(resource_model.kv_store_path)

        # generate the resource from the resource model and check its values
        new_resource: TestResourceFields = resource_model.get_resource(new_instance=True)

        self.assertEqual(new_resource.age, 12)
        self.assertEqual(new_resource.long_str, "Hello world")
        self.assertEqual(new_resource.position[0], 5)
        self.assertEqual(new_resource.position[1], 2)

    def test_resource_clone(self):
        """Test that clone"""
        resource = TestResourceFields()
        resource.position = [5, 2]
        resource.age = 12
        resource.long_str = "Hello world"

        new_resource = resource.clone()

        self.assertIsNot(resource, new_resource)
        self.assertEqual(resource.position, new_resource.position)
        self.assertEqual(resource.age, new_resource.age)
        self.assertEqual(resource.long_str, new_resource.long_str)

    def test_technical_info(self):
        robot = Robot()
        robot.add_technical_info(TechnicalInfo("key", "value", "description"))

        resource_model = ResourceModel.save_from_resource(robot, origin=ResourceOrigin.UPLOADED)

        db_resource: ResourceModel = ResourceModel.get_by_id_and_check(resource_model.id)

        robot_db: Robot = db_resource.get_resource()
        technical_info: TechnicalInfo = robot_db.technical_info.get("key")
        self.assertEqual(technical_info.key, "key")
        self.assertEqual(technical_info.value, "value")
        self.assertEqual(technical_info.short_description, "description")
