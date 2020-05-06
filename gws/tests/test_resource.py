
import unittest
import copy
from gws.prism.app import App
from gws.prism.model import Process
from gws.prism.model import Resource

class Car(Resource):
    name = "Tesla"
    speed = 0

class Start(Process):
    def run(self, params={}):
        self._output = copy.deepcopy(self._input)
        self._output.speed = params['speed']

class TestResource(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_model(self):
        car = Car()
        car.bind_listener(Start())
        message = """{
            "action":"start",
            "params":{
                "speed" : 50
            }
        }"""

        running_car = car.deal(message)
        assert isinstance(running_car, Car)
        assert car.speed == 0
        assert running_car.speed == 50