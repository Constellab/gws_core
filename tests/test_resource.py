# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import unittest

from gws_core import (BaseTestCase, GTest, Process, Resource, ResourceSet,
                      SerializedResourceData, process_decorator,
                      resource_decorator)


@resource_decorator("Car")
class Car(Resource):
    name: str
    speed: int

    def serialize_data(self) -> SerializedResourceData:
        return {
            "name": self.name,
            "speed": self.speed
        }

    def deserialize_data(self, data: SerializedResourceData) -> None:
        self.name = data['name']
        self.speed = data['speed']


# todo a checker
@process_decorator("Start")
class Start(Process):
    pass


class TestResource(BaseTestCase):

    def test_resource(self):
        GTest.print("Resource")

        c1 = Car()
        c2 = Car()

        # rs = ResourceSet()
        # self.assertEqual(len(rs), 0)

        # rs['c1'] = c1
        # rs['c2'] = c2
        # self.assertEqual(len(rs), 2)

        # self.assertTrue(rs.save())

        # rs2 = ResourceSet.get_by_id(rs.id)
        # self.assertEqual(rs, rs2)
        # self.assertEqual(len(rs2), 2)

        # self.assertEqual(rs2['c1'], c1)
        # self.assertEqual(rs2['c2'], c2)
