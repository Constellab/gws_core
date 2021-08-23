# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (CondaEnvShell, ConfigParams, Experiment,
                      ExperimentService, GTest, ProcessDecorator, ProcessIO,
                      ProcessModel, ProcessService, ProgressBar, Resource)

from tests.base_test import BaseTest

__cdir__ = os.path.abspath(os.path.dirname(__file__))


@ProcessDecorator("CondaEnvTester")
class CondaEnvTester(CondaEnvShell):
    input_specs = {}
    output_specs = {'stdout': (Resource, )}
    env_file_path = os.path.join(
        __cdir__, "testdata", "penv", "env_jwt_conda.yml")

    def build_command(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> list:
        return ["python", os.path.join(__cdir__, "testdata", "penv", "jwt_encode.py")]

    def gather_outputs(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> ProcessIO:
        res = Resource()
        res.data["encoded_string"] = self._stdout
        return {"stdout": res}


class TestProcess(BaseTest):

    async def test_conda(self):
        GTest.print("Conda")
        proc: ProcessModel = ProcessService.create_process_from_type(
            process_type=CondaEnvTester)
        self.assertFalse(CondaEnvTester.is_installed())

        experiment: Experiment = ExperimentService.create_experiment_from_process(
            process=proc)
        experiment = await ExperimentService.run_experiment(experiment=experiment, user=GTest.user)

        result: Resource = proc.output["stdout"].get_resource()
        encoded_string = result.data["encoded_string"]
        self.assertEqual(
            encoded_string,
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U")

        self.assertTrue(CondaEnvTester.is_installed())
        self.assertTrue(proc.is_finished)

        CondaEnvTester.uninstall()
        self.assertFalse(CondaEnvTester.is_installed())
