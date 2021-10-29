# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BaseTestCase, Config, FloatParam, GTest, IntParam,
                      ProcessFactory, RobotMove, TaskModel)
from gws_core.config.config_exceptions import MissingConfigsException


class TestConfig(BaseTestCase):

    def test_config(self):
        GTest.print("Config")
        specs = {
            'moving_step':  FloatParam(default_value=0.1)
        }

        config: Config = Config()
        config.set_specs(specs)
        self.assertEqual(config.get_and_check_values(), {'moving_step': 0.1})

        config.set_value('moving_step', 4.5)
        self.assertEqual(config.get_and_check_values(), {'moving_step': 4.5})
        self.assertEqual(config.get_value('moving_step'), 4.5)

        self.assert_json(config.data, {
            "specs": {
                'moving_step': {"type": "float", "default_value": 0.1, "optional": True, "visibility": "public"}
            },
            "values": {
                'moving_step': 4.5
            }
        })

        config.save()
        config2: Config = Config.get_by_id(config.id)
        self.assertEqual(config2.data, config.data)

    def test_param_to_json(self):
        param: IntParam = IntParam(default_value=1, human_name="Test", short_description="Description",
                                   min_value=1, max_value=10, allowed_values=[1, 2], unit='km')
        dict_ = param.to_json()

        self.assertEqual(dict_["type"], "int")
        self.assertEqual(dict_["default_value"], 1)
        self.assertEqual(dict_["human_name"], "Test")
        self.assertEqual(dict_["short_description"], "Description")
        self.assertEqual(dict_["min_value"], 1)
        self.assertEqual(dict_["max_value"], 10)
        self.assertEqual(dict_["allowed_values"], [1, 2])
        self.assertEqual(dict_["unit"], "km")

    def test_task_config(self):
        GTest.print("Task config")

        robot_move: TaskModel = ProcessFactory.create_task_model_from_type(
            RobotMove)
        self.assertEqual(robot_move.config.get_value("moving_step"), 0.1)
        robot_move.config.set_value("moving_step", 0.3)
        robot_move.save_full()

        config: Config = Config.get_by_id(robot_move.config.id)
        self.assertEqual(config.get_value("moving_step"), 0.3)

    def test_optional(self):
        GTest.print("Config optional")
        specs = {
            'moving_step': FloatParam(),
            'optional': FloatParam(default_value=0.1),
        }

        # Check an optional config
        config: Config = Config()
        config.set_specs(specs)
        config.set_values({"moving_step": 1.1})
        self.assertEqual(config.get_and_check_values(), {"moving_step": 1.1, "optional": 0.1})

        # Check a missing config
        config: Config = Config(specs=specs)
        config.set_specs(specs)
        config.set_values({"optional": 1.1})

        with self.assertRaises(MissingConfigsException):
            config.get_and_check_values()

    def test_param_visibility(self):
        float_1 = FloatParam(default_value=1, visibility="protected")
        float_2 = FloatParam(optional=True, visibility="private")
        self.assertRaises(Exception, FloatParam, visibility="protected")
        self.assertRaises(Exception, FloatParam, visibility="wrong")

        # Test that the config private are not returned in json
        config: Config = Config()
        config.set_specs({'float_1': float_1, 'float_2': float_2})

        json_ = config.data_to_json()
        self.assertTrue('float_1' in json_['specs'])
        self.assertFalse('float_2' in json_['specs'])
