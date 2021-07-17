# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import unittest
from gws.process import Process
from gws.resource import Resource
from gws.io import Connector
from gws.logger import Error
from gws.unittest import GTest

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

class Jump(Process):
    input_specs = {'jump_person_in_1' : Person, 'jump_person_in_2' : Person, 'jump_person_in_2' : Person}
    output_specs = {'jump_person_out' : Person}
    config_specs = {}
    async def task(self):
        return
    
class TestIO(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()
        
    def test_connect(self):
        GTest.print("IO connect")

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

        self.assertEqual(port_connect.to_json(), {
            "from": {"node": "p0",  "port": "create_person_out"},
            "to": {"node": "p1",  "port": "move_person_in"},
            'resource': {'uri': '', 'type': ''}
        })
    
    def test_iterator(self):
        GTest.print("IO Iterator")

        jump = Jump(instance_name="p3")
        for k in jump.input:
            print(k)
            print(jump.input[k])
            #self.assertEquals( jump.input[k] )