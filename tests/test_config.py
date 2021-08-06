# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import unittest

from gws_core import Config, GTest, RobotMove


class TestConfig(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_config(self):
        GTest.print("Config")
        specs = {
            'moving_step': {"type": float, "default": 0.1}
        }

        config: Config = Config(specs=specs)
        self.assertEqual(config.specs, specs)
        self.assertEqual(config.params, {'moving_step': 0.1})

        config.set_param('moving_step', 4.5)
        self.assertEqual(config.params, {'moving_step': 4.5})
        self.assertEqual(config.get_param('moving_step'), 4.5)

        self.assertEquals(config.data, {
            "specs": {
                'moving_step': {"type": "float", "default": 0.1}
            },
            "params": {
                'moving_step': 4.5
            }
        })

        config.save()
        config2: Config = Config.get_by_id(config.id)
        self.assertEqual(config2.data, config.data)

    def test_process_config(self):
        robotMove: RobotMove = RobotMove()
        self.assertEqual(robotMove.get_param("moving_step"), 0.1)
        robotMove.set_param("moving_step", 0.3)
        robotMove.save()

        config: Config = Config.get_by_id(robotMove.config.id)
        self.assertEqual(config.get_param("moving_step"), 0.3)
