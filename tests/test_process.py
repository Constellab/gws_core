
import asyncio
import unittest
from gws.prism.model import Config, Process, Config, Resource, Model, ViewModel
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

class Create(Process):
    input_specs = {}
    output_specs = {'person' : Person}
    config_specs = {'config': Config}
    async def task(self, params={}):
        print("Create")
        p = Person()
        self.output['person'] = p

class MoveConfig(Config):
    specs = {
        'moving_step': {"type": float, "default": 0.1}
    }

class Move(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    config_specs = {'default': MoveConfig}
    async def task(self):
        print(f"Moving {self.get_param('moving_step')}")
        p = Person()
        p.set_position(self._input['person'].position + self.get_param('moving_step'))
        p.set_weight(self._input['person'].weight)
        self.output['person'] = p

class EatConfig(Config):
    specs = {
        'food_weight': {"type": float, "default": 3.14}
    }

class Eat(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    config_specs = {'config': EatConfig}
    async def task(self):
        print(f"Eating {self.get_param('food_weight')}")
        p = Person()
        p.set_position(self.input['person'].position)
        p.set_weight(self.input['person'].weight + self.get_param('food_weight'))
        self.output['person'] = p

class WaitConfig(Config):
    specs = {
        'waiting_time': {"type": float, "default": 0.5} #wait for .5 secs by default
    }
class Wait(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    config_specs = {'config': WaitConfig}
    async def task(self):
        print(f"Waiting {self.get_param('waiting_time')}")
        p = Person()
        p.set_position(self.input['person'].position)
        p.set_weight(self.input['person'].weight)
        self.output['person'] = p
        await asyncio.sleep(self.get_param('waiting_time')) 

Controller.register_model_specs([Person, Move, Eat, Wait])

class TestProcess(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        Config.drop_table()
        Move.drop_table()
        Eat.drop_table()
        Wait.drop_table()
        pass

    def test_process(self):
        
        async def _process(self):
            p0 = Create()
            p1 = Move()
            p2 = Eat()
            p3 = Move()
            p4 = Move()
            p5 = Eat()
            p_wait = Wait()
            
            # create a chain
            p0>>'person'        | p1<<'person'
            p1>>'person'        | p2<<'person'
            p2>>'person'        | p_wait<<'person'
            p_wait>>'person'    | p3<<'person'
            p3>>'person'        | p4<<'person'
            p2>>'person'        | p5<<'person'

            self.assertEqual( len(p1.next_processes()), 1 )
            self.assertEqual( len(p2.next_processes()), 2 )

            p2.set_param('food_weight', '5.6')
            await p0.run()

            print("Sleeping 1 sec for waiting all tasks to finish ...")
            await asyncio.sleep(1)

            elon = p0.output['person']
            alan = elon
            self.assertEqual( elon, alan )
            self.assertTrue( elon is alan )

            self.assertEqual( elon.position, 0 )
            self.assertEqual( elon.weight, 70 )
            self.assertEqual( elon, p1.input['person'] )
            self.assertTrue( elon is p1.input['person'] )
            
            self.assertEqual( p1.data, {'inputs': {'person': p1.input['person'].uri}} )
            self.assertEqual( p_wait.data, {'inputs': {'person': p_wait.input['person'].uri}} )
            self.assertEqual( p5.data, {'inputs': {'person': p5.input['person'].uri}} )

            # check p1
            self.assertEqual( p1.output['person'].position, elon.position + p1.get_param('moving_step') )
            self.assertEqual( p1.output['person'].weight, elon.weight )

            # check p2
            self.assertEqual( p1.output['person'], p2.input['person'])
            self.assertEqual( p2.output['person'].position, p2.input['person'].position)
            self.assertEqual( p2.output['person'].weight, p2.input['person'].weight + p2.get_param('food_weight'))

            # check p3
            self.assertEqual( p_wait.output['person'], p3.input['person'])
            self.assertEqual( p3.output['person'].position, p3.input['person'].position + p3.get_param('moving_step'))
            self.assertEqual( p3.output['person'].weight, p3.input['person'].weight)
            
            #elon.save()
            #p0.save()

            res = Person.get_by_id( p3.output['person'].id )
            self.assertTrue( isinstance(res, Person) )
            self.assertEqual( res.process, p3 )
            self.assertTrue( isinstance(res.process, type(p3)) )

        asyncio.run( _process(self) )

    
        
