# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BaseTestCase, BoolParam, ConfigValues, Experiment,
                      ExperimentService, GTest, JSONDict, Resource, Shell,
                      StrParam, TaskInputs, TaskModel, TaskOutputs,
                      TaskService, task_decorator)


@task_decorator("Echo")
class Echo(Shell):
    input_specs = {}
    output_specs = {'stdout': JSONDict}
    config_specs = {'name': StrParam(optional=True, description="The name to echo"), 'save_stdout': BoolParam(
        default_value=False, description="True to save the command output text. False otherwise")}

    def build_command(self, config: ConfigValues, inputs: TaskInputs) -> list:
        name = config.get_value("name")
        return ["echo", name]

    def gather_outputs(self, config: ConfigValues, inputs: TaskInputs) -> TaskOutputs:
        res = JSONDict()
        res["out"] = self._stdout
        return {"stdout": res}


class TestShell(BaseTestCase):

    async def test_shell(self):
        GTest.print("Shell")

        proc_mdl: TaskModel = TaskService.create_task_model_from_type(
            task_type=Echo)
        proc_mdl.config.set_value("name", "John Doe")

        experiment: Experiment = ExperimentService.create_experiment_from_task_model(
            task_model=proc_mdl)

        experiment = await ExperimentService.run_experiment(experiment=experiment, user=GTest.user)

        # refresh the process
        proc_mdl = experiment.task_models[0]
        res: Resource = proc_mdl.output.get_resource_model('stdout').get_resource()
        self.assertEqual(res.data["out"], "John Doe")
