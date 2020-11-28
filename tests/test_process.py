
import asyncio
import unittest
from gws.model import Job, Config, Process, Resource, Model, ViewModel, Experiment
from gws.controller import Controller
from gws.robot import Robot, Create, Move, Eat, Wait

class TestProcess(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Job.drop_table()
        Config.drop_table()
        Create.drop_table()
        Robot.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Job.drop_table()
        Config.drop_table()
        Create.drop_table()
        Robot.drop_table()
        pass

    def test_process_singleton(self):
        p0 = Create()
        p1 = Create()

        p0.title = "First 'Create' process"
        p0.description = "This is the description of the process"
        p0.save()

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
        p0.out_port('robot')   | p1.in_port('robot')
        p1.out_port('robot')   | p2<<'robot'
        p2>>'robot'            | p_wait<<'robot'
        p_wait>>'robot'        | p3<<'robot'
        p3>>'robot'            | p4<<'robot'
        p2>>'robot'            | p5<<'robot'

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
            e = p0.create_experiment()
            await e.run()
            
            print("Sleeping 1 sec for waiting all tasks to finish ...")
            await asyncio.sleep(1)

            elon = p0.output['robot']
            alan = elon
            self.assertEqual( elon, alan )
            self.assertTrue( elon is alan )

            self.assertEqual( elon.position, 0 )
            self.assertEqual( elon.weight, 70 )
            self.assertEqual( elon, p1.input['robot'] )
            self.assertTrue( elon is p1.input['robot'] )

            # for e in p1.jobs:
            #     self.assertEqual( e.data, {'inputs': {'robot': p1.input['robot'].uri}} )
            
            # for e in p_wait.jobs:
            #     self.assertEqual( e.data, {'inputs': {'robot': p_wait.input['robot'].uri}} )
            
            # check p1
            self.assertEqual( p1.output['robot'].position, elon.position + p1.get_param('moving_step') )
            self.assertEqual( p1.output['robot'].weight, elon.weight )

            # check p2
            self.assertEqual( p1.output['robot'], p2.input['robot'])
            self.assertEqual( p2.output['robot'].position, p2.input['robot'].position)
            self.assertEqual( p2.output['robot'].weight, p2.input['robot'].weight + p2.get_param('food_weight'))

            # check p3
            self.assertEqual( p_wait.output['robot'], p3.input['robot'])
            self.assertEqual( p3.output['robot'].position, p3.input['robot'].position + p3.get_param('moving_step'))
            self.assertEqual( p3.output['robot'].weight, p3.input['robot'].weight)
            
            #elon.save()
            #p0.save()

            res = Robot.get_by_id( p3.output['robot'].id )
            self.assertTrue( isinstance(res, Robot) )

            j = res.job
            saved_proc = j.process
            self.assertEqual( saved_proc, p3 )
            self.assertTrue( saved_proc.input['robot'] is None )

        asyncio.run( _run() )

    
        
