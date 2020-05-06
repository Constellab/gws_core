
import asyncio
import unittest
from gws.prism.app import App
from gws.prism.model import Process, Resource
from gws.prism.chain import Chain

class Person(Resource):
    def __init__(self ,*args, **kwargs):
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

    async def task(self, params={}):
        print("Moving")
        self._output = Person()
        self._output.set_position(self._input.position + 5)
        self._output.set_weight(self._input.weight)

class Eat(Process):

    async def task(self, params={}):
        print("Eating")
        self._output = Person()
        self._output.set_position(self._input.position)
        self._output.set_weight(self._input.weight + 1)

class Wait(Process):

    async def task(self, params={}):
        print("Waiting")
        self._output = Person()
        self._output.set_position(self._input.position)
        self._output.set_weight(self._input.weight)
        await asyncio.sleep(.5) #wait for .5 sec



class TestProcess(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass
    
    def test_process(self):
        elon = Person()
        p1 = Move()
        p2 = Eat()
        p3 = Move()
        
        c = Chain(p1,p2,p3)


    # def test_process(self):
    #     asyncio.run( self._process() )

    # async def _process(self):
    #     elon = Person()
    #     p1 = Move()
    #     p2 = Eat()
    #     p3 = Move()
    #     p4 = Move()
    #     p5 = Eat()
        
    #     p_wait = Wait()
 
    #     # create process chains
    #     c = Chain(
    #         p1 >> p2 >> p_wait >> p3 >> p4,
    #         p2 >> p5
    #     )

    #     self.assertEqual( len(p1._next), 1 )
    #     self.assertEqual( len(p2._next), 2 )

    #     p1.set_input(elon)
    #     await p1.run()

    #     print("Sleeping 1 sec for all tasks to finish ...")
    #     await asyncio.sleep(1)

    #     alan = elon
    #     self.assertEqual( elon, alan )

    #     self.assertEqual( elon.position, 0 )
    #     self.assertEqual( elon.weight, 70 )
    #     self.assertEqual( elon, p1.input )
        
    #     # check p1
    #     self.assertEqual( p1.output.position, elon.position + 5 )
    #     self.assertEqual( p1.output.weight, elon.weight )

    #     # check p2
    #     self.assertEqual( p1.output, p2.input)
    #     self.assertEqual( p2.output.position, p2.input.position)
    #     self.assertEqual( p2.output.weight, p2.input.weight + 1)

    #     # check p3
    #     self.assertEqual( p_wait.output, p3.input)
    #     self.assertEqual( p3.output.position, p3.input.position + 5)
    #     self.assertEqual( p3.output.weight, p3.input.weight)
