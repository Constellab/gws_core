
import os
import asyncio
import unittest
import json

from gws.settings import Settings
from gws.prism.model import Config, Process, Resource, Model, ViewModel, Protocol, Job, Experiment
from gws.prism.controller import Controller

settings = Settings.retrieve()
testdata_dir = settings.get_data("gws:testdata_dir")

class Person(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = { 
            "position": 0,
            "weight": 70
        }
    
    @property
    def position(self):
        return self.data['position']

    @property
    def weight(self):
        return self.data['weight']

    def set_position(self, val):
        self.data['position'] = val

    def set_weight(self, val):
        self.data['weight'] = val

class Create(Process):
    input_specs = {}
    output_specs = {'person' : Person}
    config_specs = {}

    def task(self):
        print("Create", flush=True)
        p = Person()
        self.output['person'] = p

class Move(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    config_specs = {
        'moving_step': {"type": float, "default": 0.1}
    }

    def task(self):
        print(f"Moving {self.get_param('moving_step')}", flush=True)
        p = Person()
        p.set_position(self._input['person'].position + self.get_param('moving_step'))
        p.set_weight(self._input['person'].weight)
        self.output['person'] = p

class Eat(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    config_specs = {
        'food_weight': {"type": float, "default": 3.14}
    }

    def task(self):
        print(f"Eating {self.get_param('food_weight')}", flush=True)
        p = Person()
        p.set_position(self.input['person'].position)
        p.set_weight(self.input['person'].weight + self.get_param('food_weight'))
        self.output['person'] = p

class Wait(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    config_specs = {
        'waiting_time': {"type": float, "default": 0.5} #wait for .5 secs by default
    }

    def task(self):
        print(f"Waiting {self.get_param('waiting_time')}", flush=True)
        p = Person()
        p.set_position(self.input['person'].position)
        p.set_weight(self.input['person'].weight)
        self.output['person'] = p  
        import time
        time.sleep(self.get_param('waiting_time'))

class TestProtocol(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Config.drop_table()
        Process.drop_table()
        Protocol.drop_table()
        Experiment.drop_table()
        Job.drop_table()
        Person.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Config.drop_table()
        Process.drop_table()
        Protocol.drop_table()
        Experiment.drop_table()
        Job.drop_table()
        Person.drop_table()
        pass
    
    def test_protocol(self):
        p0 = Create()
        p1 = Move()
        p2 = Eat()
        p3 = Move()
        p4 = Move()
        p5 = Eat()
        p_wait = Wait()
        
        # create a chain
        proto = Protocol(
            processes = {
                'p0' : p0,  
                'p1' : p1, 
                'p2' : p2, 
                'p3' : p3,  
                'p4' : p4,  
                'p5' : p5, 
                'p_wait' : p_wait
            },
            connectors=[
                p0>>'person'        | p1<<'person',
                p1>>'person'        | p2<<'person',
                p2>>'person'        | p_wait<<'person',
                p_wait>>'person'    | p3<<'person',
                p3>>'person'        | p4<<'person',
                p2>>'person'        | p5<<'person'
            ],
            interfaces = {},
            outerfaces = {}
        )

        async def _run():
            await proto.run()

            print("Sleeping 1 sec for waiting all tasks to finish ...")
            await asyncio.sleep(1)

        from gws.session import Session
        e = Session.get_experiment()

        self.assertTrue(e.jobs.count(), 8)
        self.assertTrue(e.is_finished, False)
        self.assertTrue(e.is_running, False)

        asyncio.run( _run() )

    def test_connected_protocol(self):
        p0 = Create(name="p0")
        p1 = Move()
        p2 = Eat()
        p3 = Move()
        p4 = Move()
        p5 = Eat(name="p5")
        p_wait = Wait()
        
        # create a chain
        proto = Protocol(
            name = "proto",
            processes = {
                'p1' : p1, 
                'p2' : p2, 
                'p3' : p3,  
                'p4' : p4,  
                'p_wait' : p_wait
            },
            connectors=[
                p1>>'person'        | p2<<'person',
                p2>>'person'        | p_wait<<'person',
                p_wait>>'person'    | p3<<'person',
                p2>>'person'        | p4<<'person'
            ],
            interfaces = { 'person' : p1.in_port('person') },
            outerfaces = { 'person' : p2.out_port('person') }
        )

        p0>>'person'        | proto<<'person'
        proto>>'person'     | p5<<'person'

        async def _run():
            await p0.run()

            print("Sleeping 1 sec for waiting all tasks to finish ...")
            await asyncio.sleep(1)

        asyncio.run( _run() )