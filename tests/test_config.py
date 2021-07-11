# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import unittest
from gws.config import Config
from gws.unittest import GTest
from gws.robot import Move

class TestConfig(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_config(self):
        GTest.print("Test Config")

        specs = {
            'moving_step': {"type": float, "default": 0.1}
        }

        c = Config(specs=specs)
        self.assertEqual(c.specs, specs)
        self.assertEqual(c.params, {'moving_step': 0.1})

        c.set_param('moving_step', 4.5)
        self.assertEqual(c.params, {'moving_step': 4.5})
        self.assertEqual(c.get_param('moving_step'), 4.5)

        self.assertEquals(c.data, {
            "specs" : {
                'moving_step': {"type": "float", "default": 0.1}
            },
            "params":{
                'moving_step': 4.5
            }
        })

        c.save()
        c2 = Config.get_by_id(c.id)
        self.assertEqual(c2.data, c.data)


    def test_process_config(self):
        m = Move()
        self.assertEqual(m.get_param("moving_step"), 0.1)
        m.set_param("moving_step", 0.3)
        m.save()

        c = Config.get_by_id(m.config.id)
        self.assertEqual(c.get_param("moving_step"), 0.3)