
import unittest
import copy
from gws.prism.app import App
from gws.prism.model import Process
from gws.prism.model import Resource
from gws.prism.controller import Controller

class Car(Resource):
    name = "Tesla"
    speed = 0

class Start(Process):
    def run(self, params={}):
        self._output = copy.deepcopy(self._input)
        self._output.speed = params['speed']

Controller.register_models([Car, Start])

class TestResource(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_model(self):
        pass