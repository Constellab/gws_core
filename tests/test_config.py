
import asyncio
import unittest
from gws.model import Config, Process, Config, Resource, Model, ViewModel
from gws.controller import Controller


class TestConfig(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Config.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Config.drop_table()
        pass

    def test_config(self):
        
        specs = {
            'moving_step': {"type": float, "default": 0.1}
        }

        c = Config(specs=specs)

        self.assertEquals(c.specs, specs)
        self.assertEquals(c.params, {'moving_step': 0.1})

        c.set_param('moving_step', 4.5)
        self.assertEquals(c.params, {'moving_step': 4.5})
        self.assertEquals(c.get_param('moving_step'), 4.5)

        self.assertEquals(c.data, {
            "specs" : {
                'moving_step': {"type": "float", "default": 0.1}
            },
            "params":{
                'moving_step': 4.5
            }
        })

