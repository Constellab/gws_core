# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BaseTestCase, ConfigParams, Experiment,
                      ExperimentService, GTest, JSONDict, ProcessInputs,
                      ProcessModel, ProcessService, Shell, Resource, process_decorator)
from gws_core.process.process_io import ProcessOutputs


@process_decorator("Echo")
class Echo(Shell):
    input_specs = {}
    output_specs = {'stdout': JSONDict}
    config_specs = {'name': {"type": str, "default": None, 'description': "The name to echo"}, 'save_stdout': {
        "type": bool, "default": False, 'description': "True to save the command output text. False otherwise"}, }

    def build_command(self, config: ConfigParams, inputs: ProcessInputs) -> list:
        name = config.get_param("name")
        return ["echo", name]

    def gather_outputs(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        res = JSONDict()
        res["out"] = self._stdout
        return {"stdout": res}


class TestShell(BaseTestCase):

    async def test_shell(self):
        GTest.print("Shell")

        proc_mdl: ProcessModel = ProcessService.create_model_from_process_type(
            process_type=Echo)
        proc_mdl.config.set_param("name", "John Doe")

        experiment: Experiment = ExperimentService.create_experiment_from_process_model(
            process_model=proc_mdl)

        experiment = await ExperimentService.run_experiment(experiment=experiment, user=GTest.user)

        # refresh the process
        proc_mdl = experiment.processes[0]
        res: Resource = proc_mdl.output.get_resource_model('stdout').get_resource()
        self.assertEqual(res.data["out"], "John Doe")
