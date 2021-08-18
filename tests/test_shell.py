# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import IsolatedAsyncioTestCase

from gws_core import (Experiment, ExperimentService, GTest, ProcessDecorator,
                      Resource, Shell)
from gws_core.config.config import Config
from gws_core.process.process_model import ProcessModel
from gws_core.process.processable_factory import ProcessableFactory
from gws_core.progress_bar.progress_bar import ProgressBar
from gws_core.resource.io import Input, Output


@ProcessDecorator("Echo")
class Echo(Shell):
    input_specs = {}
    output_specs = {'stdout': (Resource)}
    config_specs = {
        'name': {"type": str, "default": None, 'description': "The name to echo"},
        'save_stdout': {"type": bool, "default": False, 'description': "True to save the command output text. False otherwise"},
    }

    def build_command(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> list:
        name = config.get_param("name")
        return ["echo", name]

    def gather_outputs(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar):
        res = Resource()
        res.data["out"] = self._stdout
        outputs["stdout"] = res


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

        proc: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=Echo)
        proc.set_param("name", "Jhon Doe")

        experiment: Experiment = ExperimentService.create_experiment_from_process(
            process=proc)

        experiment = await ExperimentService.run_experiment(experiment=experiment, user=GTest.user)
        res = proc.output['stdout']
        self.assertEqual(res.data["out"], "Jhon Doe")
