# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BaseTestCase, ConfigParams, Experiment,
                      ExperimentService, File, GTest, JSONDict, PipEnvShell,
                      Resource, Settings, ShellProxy, TaskInputs, TaskModel,
                      TaskOutputs, TaskService, task_decorator)
from gws_core.experiment.experiment_run_service import ExperimentRunService

settings = Settings.retrieve()
test_datadir = settings.get_variable("gws_core:testdata_dir")
__cdir__ = os.path.dirname(os.path.realpath(__file__))


@task_decorator("PipEnvTester")
class PipEnvTester(PipEnvShell):
    input_specs = {}
    output_specs = {'file': (File, )}
    env_file_path = os.path.join(__cdir__, "penv", "env_jwt_pip.txt")

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        return ["python", os.path.join(__cdir__, "penv", "jwt_encode.py"), ">", "out.txt"]

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        file = File(path=os.path.join(self.working_dir, "out.txt"))
        return {"file": file}


class TestProcess(BaseTestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        PipEnvTester.uninstall()

    async def test_pipenv(self):

        GTest.print("Pipenv")
        PipEnvTester.uninstall()
        proc_mdl: TaskModel = TaskService.create_task_model_from_type(
            task_type=PipEnvTester)
        self.assertFalse(PipEnvTester.is_installed())

        experiment: Experiment = ExperimentService.create_experiment_from_task_model(
            task_model=proc_mdl)
        experiment = await ExperimentRunService.run_experiment(experiment=experiment)

        # refresh the task
        task_model: TaskModel = experiment.task_models[0]

        file: Resource = task_model.outputs.get_resource_model("file").get_resource()
        self.assertEqual(
            file.read().strip(),
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U")

        self.assertTrue(PipEnvTester.is_installed())
        self.assertTrue(task_model.is_finished)

        PipEnvTester.uninstall()
        self.assertFalse(PipEnvTester.is_installed())

    async def test_pipenv_proxy(self):
        GTest.print("Pipenv proxy")

        prox = ShellProxy(PipEnvTester)
        encoded_string = prox.check_output(
            ["python", os.path.join(__cdir__, "penv", "jwt_encode.py")]
        )
        # print(result)
        self.assertEqual(
            encoded_string,
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U")
