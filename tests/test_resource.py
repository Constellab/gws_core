# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import copy
import unittest

from gws_core import (GTest, Process, ProcessDecorator, Resource,
                      ResourceDecorator, ResourceSet)


@ResourceDecorator("Car")
class Car(Resource):
    @property
    def name(self):
        return self.data['name']

    def set_name(self, name):
        self.data['name'] = name

    @property
    def speed(self):
        return self.data['name']

    def set_speed(self, name):
        self.data['name'] = name


@ProcessDecorator("Start")
class Start(Process):
    def run(self, params={}):
        self._output = copy.deepcopy(self._input)
        self._output.set_speed(params['speed'])


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
