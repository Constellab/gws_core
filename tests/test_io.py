
import unittest
from gws.model import Process, Resource
from gws.io import Connector
from gws.logger import Error

class Person(Resource):
    pass

class Car(Resource):
    pass

class Create(Process):
    input_specs = {}
    output_specs = {'create_person_out' : Person}
    config_specs = {}
    async def task(self):
        return

class Move(Process):
    input_specs = {'move_person_in' : Person}
    output_specs = {'move_person_out' : Person}
    config_specs = {}
    async def task(self):
        return

class Drive(Process):
    input_specs = {'move_drive_in' : Car}
    output_specs = {'move_drive_out' : Car}
    config_specs = {}
    async def task(self):
        return


class TestIO(unittest.TestCase):
    
    def test_connect(self):
        p0 = Create(instance_name="p0")
        p1 = Move(instance_name="p1")
        p2 = Move(instance_name="p2")
        
        # create a chain
        port_connect = p0.out_port('create_person_out')   | p1.in_port('move_person_in')
        p1>>'move_person_out' | p2<<'move_person_in'
        
        out_port = p0.out_port('create_person_out')
        self.assertEqual(out_port.name, 'create_person_out')

        in_port = p1.in_port('move_person_in')
        self.assertEqual(in_port.name, 'move_person_in')

        self.assertIsInstance(port_connect, Connector)
        
        # assert error
        p3 = Drive(instance_name="p3")
        self.assertRaises(Exception, p2.out_port('move_person_out').pipe,  p3.in_port('move_drive_in'))

        self.assertEquals(port_connect.as_json(), {
            "from": {"node": "p0",  "port": "create_person_out"},
            "to": {"node": "p1",  "port": "move_person_in"}
        })
