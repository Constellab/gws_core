
import asyncio
import unittest
from gws.prism.model import Job, Config, Process, Resource, Model, ViewModel
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
    config_specs = {}
    async def task(self):
        print("Create")
        p = Person()
        self.output['person'] = p

class Move(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    config_specs = {
        'moving_step': {"type": 'float', "default": 0.1}
    }
    async def task(self):
        print(f"Moving {self.get_param('moving_step')}")
        p = Person()
        p.set_position(self._input['person'].position + self.get_param('moving_step'))
        p.set_weight(self._input['person'].weight)
        self.output['person'] = p

class Eat(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    config_specs = {
        'food_weight': {"type": 'float', "default": 3.14}
    }
    async def task(self):
        print(f"Eating {self.get_param('food_weight')}")
        p = Person()
        p.set_position(self.input['person'].position)
        p.set_weight(self.input['person'].weight + self.get_param('food_weight'))
        self.output['person'] = p

class Wait(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    config_specs = {
        'waiting_time': {"type": 'float', "default": 0.5} #wait for .5 secs by default
    }
    async def task(self):
        print(f"Waiting {self.get_param('waiting_time')}")
        p = Person()
        p.set_position(self.input['person'].position)
        p.set_weight(self.input['person'].weight)
        self.output['person'] = p
        await asyncio.sleep(self.get_param('waiting_time')) 


class TestProcess(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        Job.drop_table()
        Config.drop_table()
        Person.drop_table()
        Move.drop_table()
        Eat.drop_table()
        Wait.drop_table()
        pass

    def test_process_singleton(self):
        p0 = Create()
        p1 = Create()

        self.assertTrue(p0.id == p1.id) 
        self.assertTrue(not p0 is p1)
        self.assertTrue(not p0.id is None)
        self.assertTrue(not p1.id is None)

    def test_process(self):
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

        rules = p0.output.links()
        self.assertEqual(rules, [
            {'from': {'node': p0, 'port': 'person'}, 'to': {'node': p1, 'port': 'person'}}
        ])

        rules = p2.output.links()
        self.assertEqual(rules, [
            {'from': {'node': p2, 'port': 'person'}, 'to': {'node': p_wait, 'port': 'person'}},
            {'from': {'node': p2, 'port': 'person'}, 'to': {'node': p5, 'port': 'person'}},
        ])

        self.assertEqual( len(p1.get_next_procs()), 1 )
        self.assertEqual( len(p2.get_next_procs()), 2 )

        p2.set_param('food_weight', '5.6')
        
        async def _on_p3_start( proc ):
            self.assertEqual( proc, p3 )

        async def _on_p5_start( proc ):
            self.assertEqual( proc, p5 )

        async def _on_p5_end( proc ):
            self.assertEqual( proc, p5 )

        async def _run():
            
            # set events
            p3.on_start = _on_p3_start
            p5.on_start = _on_p5_start
            p5.on_end = _on_p5_end

            # start
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

            # for e in p1.jobs:
            #     self.assertEqual( e.data, {'inputs': {'person': p1.input['person'].uri}} )
            
            # for e in p_wait.jobs:
            #     self.assertEqual( e.data, {'inputs': {'person': p_wait.input['person'].uri}} )
            
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

            e = res.job
            saved_proc = e.process
            self.assertEqual( saved_proc, p3 )
            self.assertTrue( saved_proc.input['person'] is None )

        asyncio.run( _run() )

    
        
