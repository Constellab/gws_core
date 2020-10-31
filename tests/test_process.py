
import asyncio
import unittest
from gws.model import Job, Config, Process, Resource, Model, ViewModel, Experiment
from gws.controller import Controller
from gws.hello import Person, Create, Move, Eat, Wait

class TestProcess(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Job.drop_table()
        Config.drop_table()
        Create.drop_table()
        Person.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Job.drop_table()
        Config.drop_table()
        Create.drop_table()
        Person.drop_table()
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
        p0.out_port('person')   | p1.in_port('person')
        p1.out_port('person')   | p2<<'person'
        p2>>'person'            | p_wait<<'person'
        p_wait>>'person'        | p3<<'person'
        p3>>'person'            | p4<<'person'
        p2>>'person'            | p5<<'person'

        self.assertEqual( len(p1.get_next_procs()), 1 )
        self.assertEqual( len(p2.get_next_procs()), 2 )

        p2.set_param('food_weight', '5.6')
        
        def _on_p3_start( proc ):
            self.assertEqual( proc, p3 )

        def _on_p5_start( proc ):
            self.assertEqual( proc, p5 )

        def _on_p5_end( proc ):
            self.assertEqual( proc, p5 )

        async def _run():
            
            # set events
            p3.on_start(_on_p3_start)
            p5.on_start(_on_p5_start)
            p5.on_end(_on_p5_end)

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

    
        
