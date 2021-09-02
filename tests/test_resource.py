# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import unittest

from gws_core import (GTest, Process, ProcessDecorator, Resource,
                      ResourceDecorator, ResourceSet)
from gws_core.resource.resource_serialized import ResourceSerialized


@ResourceDecorator("Car")
class Car(Resource):

    name: str
    speed: int

    def serialize(self) -> ResourceSerialized:
        return ResourceSerialized(light_data={
            "name": self.name,
            "speed": self.speed
        })

    def deserialize(self, resource_serialized: ResourceSerialized) -> None:
        self.name = resource_serialized.light_data['name']
        self.speed = resource_serialized.light_data['speed']


# todo a checker


@ProcessDecorator("Start")
class Start(Process):
    pass


class TestResource(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_resource(self):
        GTest.print("Resource")

        c1 = Car()
        c2 = Car()

        rs = ResourceSet()
        self.assertEqual(len(rs), 0)

        rs['c1'] = c1
        rs['c2'] = c2
        self.assertEqual(len(rs), 2)

        self.assertTrue(rs.save())

        rs2 = ResourceSet.get_by_id(rs.id)
        self.assertEqual(rs, rs2)
        self.assertEqual(len(rs2), 2)

        self.assertEqual(rs2['c1'], c1)
        self.assertEqual(rs2['c2'], c2)
