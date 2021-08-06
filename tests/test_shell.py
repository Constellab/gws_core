# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
from unittest import IsolatedAsyncioTestCase

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


class TestShell(IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    async def test_shell(self):
        GTest.print("Shell")

        proc = Echo()
        proc.set_param("name", "Jhon Doe")
        experiment: Experiment = proc.create_experiment(
            study=GTest.study, user=GTest.user)

        experiment = await ExperimentService.run_experiment(experiment=experiment, user=GTest.user)
        res = proc.output['stdout']
        self.assertEqual(res.data["out"], "Jhon Doe")
