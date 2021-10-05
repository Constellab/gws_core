# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BaseTestCase, ConfigParams, Experiment,
                      ExperimentService, GTest, JSONDict, PipEnvShell,
                      Resource, TaskInputs, TaskModel, TaskOutputs,
                      TaskService, task_decorator)

__cdir__ = os.path.abspath(os.path.dirname(__file__))


@task_decorator("PipEnvTester")
class PipEnvTester(PipEnvShell):
    input_specs = {}
    output_specs = {'stdout': (JSONDict, )}
    env_file_path = os.path.join(
        __cdir__, "../", "testdata", "penv", "env_jwt_pip.txt")

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        return ["python", os.path.join(__cdir__, "testdata", "penv", "jwt_encode.py")]

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        res = JSONDict()
        res["encoded_string"] = self._stdout
        return {"stdout": res}


class TestProcess(BaseTestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        PipEnvTester.uninstall()

    async def test_pipenv(self):

        GTest.print("Pipenv")
        proc_mdl: TaskModel = TaskService.create_task_model_from_type(
            task_type=PipEnvTester)
        self.assertFalse(PipEnvTester.is_installed())

        experiment: Experiment = ExperimentService.create_experiment_from_task_model(
            task_model=proc_mdl)
        experiment = await ExperimentService.run_experiment(experiment=experiment, user=GTest.user)

        # refresh the task
        task_model: TaskModel = experiment.task_models[0]

        result: Resource = task_model.outputs.get_resource_model("stdout").get_resource()
        encoded_string = result.data["encoded_string"]
        self.assertEqual(
            encoded_string,
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U")

        self.assertTrue(PipEnvTester.is_installed())
        self.assertTrue(task_model.is_finished)

        PipEnvTester.uninstall()
        self.assertFalse(PipEnvTester.is_installed())
