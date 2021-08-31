# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import Config, GTest, RobotMove
from gws_core.config.config_exceptions import MissingConfigsException
from gws_core.process.process_model import ProcessModel
from gws_core.processable.processable_factory import ProcessableFactory

from tests.base_test import BaseTest


class TestConfig(BaseTest):

    def test_config(self):
        GTest.print("Config")
        specs = {
            'moving_step': {"type": float, "default": 0.1}
        }

        config: Config = Config(specs=specs)
        self.assertEqual(config.specs, specs)
        self.assertEqual(config.get_and_check_params(), {'moving_step': 0.1})

        config.set_param('moving_step', 4.5)
        self.assertEqual(config.get_and_check_params(), {'moving_step': 4.5})
        self.assertEqual(config.get_param('moving_step'), 4.5)

        self.assertEqual(config.data, {
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
        GTest.print("Process config")

        robotMove: ProcessModel = ProcessableFactory.create_process_model_from_type(
            RobotMove)
        self.assertEqual(robotMove.get_param("moving_step"), 0.1)
        robotMove.set_param("moving_step", 0.3)
        robotMove.save_full()

        config: Config = Config.get_by_id(robotMove.config.id)
        self.assertEqual(config.get_param("moving_step"), 0.3)

    def test_optional(self):
        GTest.print("Config optional")
        specs = {
            'moving_step': {"type": float},
            'optional': {"type": float, "default": 0.1},
        }

        # Check an optional config
        config: Config = Config(specs=specs)
        config.set_params({"moving_step": 1.1})
        self.assertEqual(config.get_and_check_params(), {"moving_step": 1.1, "optional": 0.1})

        # Check a missing config
        config: Config = Config(specs=specs)
        config.set_params({"optional": 1.1})

        with self.assertRaises(MissingConfigsException):
            config.get_and_check_params()
