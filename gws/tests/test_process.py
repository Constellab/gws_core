
import asyncio
import unittest
from gws.prism.app import App
from gws.prism.model import Process, Resource, Model, ViewModel
from gws.prism.controller import Controller

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

class Move(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    async def task(self, params={}):
        print("Moving")
        p = Person()
        p.set_position(self._input['person'].position + params['moving_step'])
        p.set_weight(self._input['person'].weight)
        self.output['person'] = p

class Eat(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    async def task(self, params={}):
        print("Eating")
        p = Person()
        p.set_position(self.input['person'].position)
        p.set_weight(self.input['person'].weight + params['food_weight'])
        self.output['person'] = p

class Wait(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    async def task(self, params={}):
        print("Waiting")
        p = Person()
        p.set_position(self.input['person'].position)
        p.set_weight(self.input['person'].weight)
        self.output['person'] = p
        await asyncio.sleep(.5) #wait for .5 sec

class TestProcess(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Person.drop_table()
        Move.drop_table()
        Eat.drop_table()
        Wait.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        Move.drop_table()
        Eat.drop_table()
        Wait.drop_table()
        pass

    def test_process(self):
        asyncio.run( self._process() )

    async def _process(self):
        elon = Person()
        p1 = Move()
        p2 = Eat()
        p3 = Move()
        p4 = Move()
        p5 = Eat()
        p_wait = Wait()
 
        # create a chain
        p1>>'person'        | p2<<'person'
        p2>>'person'        | p_wait<<'person'
        p_wait>>'person'    | p3<<'person'
        p3>>'person'        | p4<<'person'
        p2>>'person'        | p5<<'person'

        self.assertEqual( len(p1.next_processes()), 1 )
        self.assertEqual( len(p2.next_processes()), 2 )

        p1.input['person'] = elon
        params = {'moving_step': 5, 'food_weight': 2}
        await p1.run(params)

        print("Sleeping 1 sec for waiting all tasks to finish ...")
        await asyncio.sleep(1)

        alan = elon
        self.assertEqual( elon, alan )
        self.assertTrue( elon is alan )

        self.assertEqual( elon.position, 0 )
        self.assertEqual( elon.weight, 70 )
        self.assertEqual( elon, p1.input['person'] )
        self.assertTrue( elon is p1.input['person'] )
        
        self.assertEqual( p1.data, params )
        self.assertEqual( p_wait.data, params)
        self.assertEqual( p5.data, params)

        # check p1
        self.assertEqual( p1.output['person'].position, elon.position + params['moving_step'] )
        self.assertEqual( p1.output['person'].weight, elon.weight )

        # check p2
        self.assertEqual( p1.output['person'], p2.input['person'])
        self.assertEqual( p2.output['person'].position, p2.input['person'].position)
        self.assertEqual( p2.output['person'].weight, p2.input['person'].weight + params['food_weight'])

        # check p3
        self.assertEqual( p_wait.output['person'], p3.input['person'])
        self.assertEqual( p3.output['person'].position, p3.input['person'].position + params['moving_step'])
        self.assertEqual( p3.output['person'].weight, p3.input['person'].weight)

        Controller.save_all()