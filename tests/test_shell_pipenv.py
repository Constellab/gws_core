# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, Experiment, ExperimentService, GTest,
                      PipEnvShell, ProcessDecorator, ProcessIO, ProcessModel,
                      ProcessService, ProgressBar, Resource)

from tests.base_test import BaseTest

__cdir__ = os.path.abspath(os.path.dirname(__file__))


@ProcessDecorator("PipEnvTester")
class PipEnvTester(PipEnvShell):
    input_specs = {}
    output_specs = {'stdout': (Resource, )}
    env_file_path = os.path.join(
        __cdir__, "testdata", "penv", "env_jwt_pip.txt")

    def build_command(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> list:
        return ["python", os.path.join(__cdir__, "testdata", "penv", "jwt_encode.py")]

    def gather_outputs(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> ProcessIO:
        res = Resource()
        res.data["encoded_string"] = self._stdout
        return {"stdout": res}


class TestProcess(BaseTest):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        PipEnvTester.uninstall()

    async def test_pipenv(self):

        GTest.print("Pipenv")
        proc: ProcessModel = ProcessService.create_process_from_type(
            process_type=PipEnvTester)
        self.assertFalse(PipEnvTester.is_installed())

        experiment: Experiment = ExperimentService.create_experiment_from_process(
            process=proc)
        experiment = await ExperimentService.run_experiment(experiment=experiment, user=GTest.user)

        # refresh the process
        proc = experiment.processes[0]

        result: Resource = proc.output["stdout"].get_resource()
        encoded_string = result.data["encoded_string"]
        self.assertEqual(
            encoded_string,
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U")

        self.assertTrue(PipEnvTester.is_installed())
        self.assertTrue(proc.is_finished)

        PipEnvTester.uninstall()
        self.assertFalse(PipEnvTester.is_installed())
