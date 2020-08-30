
import unittest
import copy
from gws.app import App
from gws.prism.model import Process
from gws.prism.model import Resource, ResourceSet
from gws.prism.controller import Controller

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

class Start(Process):
    def run(self, params={}):
        self._output = copy.deepcopy(self._input)
        self._output.set_speed(params['speed'])

class TestResource(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_model(self):

        c1 = Car()
        c2 = Car()

        rs = ResourceSet()
        self.assertEquals(len(rs), 0)

        rs['c1'] = c1
        rs['c2'] = c2
        self.assertEquals(len(rs), 2)
        
        self.assertTrue(rs.save())

        rs2 = ResourceSet.get_by_id(rs.id)
        self.assertEquals(rs, rs2)
        self.assertEquals(len(rs2),2)

        self.assertEquals(rs2['c1'],c1)
        self.assertEquals(rs2['c2'],c2)