

from numpy import NaN
from pandas.core.frame import DataFrame

from gws_core import (BaseTestCase, BoolRField, DataFrameRField, DictRField,
                      FloatRField, IntRField, KVStore, ListRField,
                      ResourceModel, ResourceRField, SerializableObjectJson,
                      SerializableRField, StrRField)
from gws_core.impl.robot.robot_resource import Robot
from gws_core.resource.resource_dto import ResourceOrigin


class TestJsonableObject(SerializableObjectJson):
    name: str

    def __init__(self, name: str):
        self.name = name

    def serialize(self) -> dict:
        return {"name": self.name}

    @classmethod
    def deserialize(cls, json_data: dict):
        return TestJsonableObject(json_data["name"])


# test_r_field
class TestRField(BaseTestCase):

    def test_int_r_field(self):
        r_field = IntRField(-1)

        self.assertEqual(r_field.get_default_value(), -1)
        self.assertEqual(r_field.serialize(3), 3)
        self.assertEqual(r_field.serialize("3"), 3)
        self.assertEqual(r_field.serialize(None), -1)

        self.assertEqual(r_field.deserialize(3), 3)
        self.assertEqual(r_field.deserialize("3"), 3)
        self.assertEqual(r_field.deserialize(None), -1)

        self.assertRaises(Exception, r_field.serialize, "tt")
        self.assertRaises(Exception, r_field.deserialize, "tt")

    def test_float_r_field(self):
        r_field = FloatRField(-1.1)

        self.assertEqual(r_field.get_default_value(), -1.1)
        self.assertEqual(r_field.serialize(3.1), 3.1)
        self.assertEqual(r_field.serialize("3.1"), 3.1)
        self.assertEqual(r_field.serialize(None), -1.1)

        self.assertEqual(r_field.deserialize(3.1), 3.1)
        self.assertEqual(r_field.deserialize("3.1"), 3.1)
        self.assertEqual(r_field.deserialize(None), -1.1)

        self.assertRaises(Exception, r_field.serialize, "tt")
        self.assertRaises(Exception, r_field.deserialize, "tt")

    def test_bool_r_field(self):
        r_field = BoolRField(False)

        self.assertEqual(r_field.get_default_value(), False)
        self.assertEqual(r_field.serialize(True), True)
        self.assertEqual(r_field.serialize(None), False)

        self.assertEqual(r_field.deserialize(True), True)
        self.assertEqual(r_field.deserialize(None), False)

        self.assertRaises(Exception, r_field.serialize, "tt")
        self.assertRaises(Exception, r_field.deserialize, "tt")

    def test_str_r_field(self):
        r_field = StrRField(default_value="")

        self.assertEqual(r_field.get_default_value(), "")
        self.assertEqual(r_field.serialize("AAA"), "AAA")
        self.assertEqual(r_field.serialize(None), "")

        self.assertEqual(r_field.deserialize("AAA"), "AAA")
        self.assertEqual(r_field.deserialize(None), "")

        self.assertRaises(Exception, r_field.serialize, ["tt"])
        self.assertRaises(Exception, r_field.deserialize, ["tt"])

    def test_dict_r_field(self):
        default_value = {"test": 12}
        r_field = DictRField(default_value=default_value)

        # Check that the default value returned a new instance
        self.assertFalse(default_value is r_field.get_default_value())

        self.assertEqual(r_field.get_default_value(), {"test": 12})
        self.assertEqual(r_field.serialize({"test": 12}), {"test": 12})
        self.assertEqual(r_field.serialize(None), {"test": 12})
        self.assertEqual(r_field.serialize({"test": NaN}), {"test": None})

        self.assertEqual(r_field.deserialize({"test": 12}), {"test": 12})
        self.assertEqual(r_field.deserialize(None), {"test": 12})

        self.assertRaises(Exception, r_field.serialize, "tt")
        self.assertRaises(Exception, r_field.deserialize, "tt")

    def test_list_r_field(self):
        default_value = [1, 2]
        r_field = ListRField(default_value=default_value)

        # Check that the default value returned a new instance
        self.assertFalse(default_value is r_field.get_default_value())

        self.assertEqual(r_field.get_default_value(), default_value)
        self.assertEqual(r_field.serialize([1, 2]), [1, 2])
        self.assertEqual(r_field.serialize(None), default_value)

        self.assertEqual(r_field.deserialize([1, 2]), [1, 2])
        self.assertEqual(r_field.deserialize(None), default_value)

        self.assertRaises(Exception, r_field.serialize, "tt")
        self.assertRaises(Exception, r_field.deserialize, "tt")

    def test_dataframe_r_field(self):
        r_field = DataFrameRField()

        # Test default value
        self.assertIsInstance(r_field.get_default_value(), DataFrame)

        kv_store: KVStore = KVStore.from_filename('test_dataframe_r_field')
        path = str(kv_store.generate_new_file())

        # Test dumping and reload dataframe on file
        value = DataFrame.from_dict({"test": [1, 2]})
        r_field.dump_to_file(value, path)
        new_dataframe = r_field.load_from_file(path)

        self.assertEqual(value.to_dict(), new_dataframe.to_dict())

    def test_resource_r_field(self):
        resource_model = ResourceModel.save_from_resource(Robot.empty(), origin=ResourceOrigin.UPLOADED)
        robot: Robot = resource_model.get_resource()

        r_field = ResourceRField()
        resource_serialized = r_field.serialize(robot)
        resource_deserilized: Robot = r_field.deserialize(resource_serialized)

        self.assertEqual(robot.get_model_id(), resource_deserilized.get_model_id())
        self.assertEqual(robot.age, resource_deserilized.age)
        self.assertEqual(robot.position, resource_deserilized.position)
        self.assertEqual(robot.weight, resource_deserilized.weight)

    def test_jsonable_object_r_field(self):

        r_field = SerializableRField(TestJsonableObject)
        value = TestJsonableObject("test")
        serialized = r_field.serialize(value)
        deserialized: TestJsonableObject = r_field.deserialize(serialized)

        self.assertIsInstance(deserialized, TestJsonableObject)
        self.assertEqual(value.name, deserialized.name)
