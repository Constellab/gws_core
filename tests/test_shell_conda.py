# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from unittest import IsolatedAsyncioTestCase

from gws_core import (CondaEnvShell, Experiment, ExperimentService, GTest,
                      Resource)

__cdir__ = os.path.abspath(os.path.dirname(__file__))
class CondaEnvTester(CondaEnvShell):
    input_specs = {}
    output_specs = {'stdout': (Resource, )}
    env_file_path = os.path.join(__cdir__, "testdata", "penv", "env_jwt_conda.yml")

    def build_command(self) -> list:
        return [ "python", os.path.join(__cdir__, "testdata", "penv", "jwt_encode.py") ]

    def gather_outputs(self):
        res = Resource()
        res.data["encoded_string"] = self._stdout
        self.output["stdout"] = res

class TestProcess(IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()
        CondaEnvTester.uninstall()

    async def test_conda(self):
        GTest.print("Conda")
        proc = CondaEnvTester()
        self.assertFalse(CondaEnvTester.is_installed())

        experiment: Experiment = ExperimentService.create_experiment_from_process(
            process=proc)
        experiment = await ExperimentService.run_experiment(experiment=experiment, user=GTest.user)


        result = proc.output["stdout"]
        encoded_string = result.data["encoded_string"]
        self.assertEqual(encoded_string, "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U")

        self.assertTrue(CondaEnvTester.is_installed())
        self.assertTrue(proc.is_finished)

        CondaEnvTester.uninstall()
        self.assertFalse(proc.is_installed())

