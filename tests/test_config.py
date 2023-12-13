# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BaseTestCase, Config, FloatParam, ProcessFactory,
                      RobotMove, TaskModel)
from gws_core.config.config_exceptions import MissingConfigsException
from gws_core.config.config_params import ConfigParams
from gws_core.config.param.param_spec_helper import ParamSpecHelper


# test_config
class TestConfig(BaseTestCase):

    def test_config(self):
        specs = {
            'moving_step':  FloatParam(default_value=0.1)
        }

        config: Config = Config()
        config.set_specs(specs)

        config_params = ParamSpecHelper.build_config_params(
            config.get_specs(), config.get_values())
        self.assertIsInstance(config_params, ConfigParams)
        self.assertEqual(config_params["moving_step"], 0.1)

        config.set_value('moving_step', 4.5)
        self.assertEqual(config.get_and_check_values(), {'moving_step': 4.5})
        self.assertEqual(config.get_value('moving_step'), 4.5)

        self.assert_json(config.data, {"specs": {'moving_step': {"type": "float", "default_value": 0.1, "optional": True,
                         "visibility": "public", "additional_info": {"min_value": None, "max_value": None}}, }, "values": {'moving_step': 4.5}})

        config.save()
        config2: Config = Config.get_by_id(config.id)
        self.assertEqual(config2.data, config.data)

    def test_task_config(self):

        robot_move: TaskModel = ProcessFactory.create_task_model_from_type(
            RobotMove)
        self.assertEqual(robot_move.config.get_value("moving_step"), 0.1)
        robot_move.config.set_value("moving_step", 0.3)
        robot_move.save_full()

        config: Config = Config.get_by_id(robot_move.config.id)
        self.assertEqual(config.get_value("moving_step"), 0.3)

    def test_optional(self):
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

        json_specs = config.to_dto().specs
        self.assertTrue('float_1' in json_specs)
        self.assertFalse('float_2' in json_specs)
