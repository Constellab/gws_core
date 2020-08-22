
import unittest
import copy
from gws.app import App
from gws.prism.model import Process
from gws.prism.model import Resource
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
        pass