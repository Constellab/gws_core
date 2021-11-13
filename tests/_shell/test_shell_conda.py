# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BaseTestCase, CondaEnvShell, ConfigParams, Experiment,
                      ExperimentService, File, GTest, JSONDict, Resource,
                      Settings, TaskInputs, TaskModel, TaskOutputs,
                      TaskService, task_decorator)

settings = Settings.retrieve()
test_datadir = settings.get_variable("gws_core:testdata_dir")

__cdir__ = os.path.dirname(os.path.realpath(__file__))


@task_decorator("CondaEnvTester")
class CondaEnvTester(CondaEnvShell):
    input_specs = {}
    output_specs = {'file': (File, )}
    env_file_path = os.path.join(__cdir__, "penv", "env_jwt_conda.yml")

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        return [
            "python", os.path.join(__cdir__, "penv", "jwt_encode.py"), ">", "out.txt"
        ]

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        file = File(path=os.path.join(self.working_dir, "out.txt"))
        return {"file": file}


class TestProcess(BaseTestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        CondaEnvTester.uninstall()

    async def test_conda(self):
        GTest.print("Conda")
        proc_mdl: TaskModel = TaskService.create_task_model_from_type(
            task_type=CondaEnvTester)
        self.assertFalse(CondaEnvTester.is_installed())

        experiment: Experiment = ExperimentService.create_experiment_from_task_model(
            task_model=proc_mdl)
        experiment = await ExperimentService.run_experiment(experiment=experiment, user=GTest.user)

        proc = experiment.task_models[0]

        file: Resource = proc.outputs.get_resource_model("file").get_resource()
        self.assertEqual(
            file.read().strip(),
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U")

        self.assertTrue(CondaEnvTester.is_installed())
        self.assertTrue(proc.is_finished)

        CondaEnvTester.uninstall()
        self.assertFalse(CondaEnvTester.is_installed())
