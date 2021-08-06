# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import unittest

from gws_core import Experiment, ExperimentService, GTest, Resource, Shell


class Echo(Shell):
    input_specs = {}
    output_specs = {'stdout': (Resource, )}
    config_specs = {
        'name': {"type": str, "default": None, 'description': "The name to echo"},
        'save_stdout': {"type": bool, "default": False, 'description': "True to save the command output text. False otherwise"},
    }

    def build_command(self) -> list:
        name = self.get_param("name")
        return ["echo", name]

    def gather_outputs(self):
        res = Resource()
        res.data["out"] = self._stdout
        self.output["stdout"] = res


class TestShell(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_shell(self):
        GTest.print("Shell")

        proc = Echo()
        proc.set_param("name", "Jhon Doe")
        experiment: Experiment = proc.create_experiment(
            study=GTest.study, user=GTest.user)

        def _on_end(*args, **kwargs):
            res = proc.output['stdout']
            self.assertEqual(res.data["out"], "Jhon Doe")

        # todo check
        experiment.on_end(_on_end)
        # use the _run_experiment to have the same instance and so get the end event
        asyncio.run(ExperimentService._run_experiment(
            experiment=experiment, user=GTest.user))
