

import os
from typing import Type
from unittest import TestCase

from gws_core import File, PyCondaAgent, Task, TaskRunner
from gws_core.config.param.param_spec import IntParam, ListParam
from gws_core.core.classes.observer.message_level import MessageLevel
from gws_core.core.utils.settings import Settings
from gws_core.impl.agent.py_mamba_agent import PyMambaAgent
from gws_core.impl.agent.py_pipenv_agent import PyPipenvAgent
from gws_core.impl.agent.r_conda_agent import RCondaAgent
from gws_core.impl.agent.r_mamba_agent import RMambaAgent
from gws_core.impl.file.file_helper import FileHelper
from pandas import DataFrame, read_csv


# test_env_agent
class TestEnvAgent(TestCase):

    def test_pip_env_agent(self):
        self._test_default_config(PyPipenvAgent)

    def test_conda_env_agent(self):
        self._test_default_config(PyCondaAgent)

    def test_r_conda_env_agent(self):
        self._test_default_config(RCondaAgent)

    def test_mamba_env_agent(self):
        self._test_default_config(PyMambaAgent)

    def test_r_mamba_env_agent(self):
        self._test_default_config(RMambaAgent)

    def _test_default_config(self, task_type: Type[Task]):
        """Test the default env agent config template to be sure it is valid
        """

        # create a csv file
        data = DataFrame({'col1': [0, 1], 'col2': [0, 2]}, index=['a', 'b'])
        temp_dir = Settings.make_temp_dir()
        source = os.path.join(temp_dir, "source.csv")
        data.to_csv(source, index=True)

        tester = TaskRunner(
            task_type=task_type,
            inputs={"source": File(source)},
            params={
                'params': {}
            }
        )

        outputs = tester.run()

        target: File = outputs["target"]

        self.assertTrue(isinstance(target, File))
        target_data: DataFrame = read_csv(target.path, header=0, index_col=0, sep=',')

        self.assertTrue(target_data.T.equals(data))

        FileHelper.delete_dir(temp_dir)

    def test_agent_with_exception(self):
        tester = TaskRunner(
            params={
                "params": {},
                "code": """
raise Exception('This is not working')
""",
            },
            task_type=PyPipenvAgent
        )

        logger = tester.add_log_observer()

        error = False
        try:
            tester.run()
        except Exception:
            error = True
            # check that the error of the snippet is the same as the one raised
            self.assertTrue(logger.has_message_containing('This is not working',
                                                          level=MessageLevel.ERROR))

        self.assertTrue(error)
        tester.run_after_task()
