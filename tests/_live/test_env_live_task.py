# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import Type
from unittest import TestCase

from pandas import DataFrame, read_csv

from gws_core import File, PyCondaLiveTask, Task, TaskRunner
from gws_core.core.classes.observer.message_level import MessageLevel
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.live.py_mamba_live_task import PyMambaLiveTask
from gws_core.impl.live.py_pipenv_live_task import PyPipenvLiveTask
from gws_core.impl.live.r_conda_live_task import RCondaLiveTask
from gws_core.impl.live.r_mamba_live_task import RMambaLiveTask


# test_env_live_task
class TestEnvLiveTask(TestCase):

    def test_pip_env_live_task(self):
        self._test_default_config(PyPipenvLiveTask)

    def test_conda_env_live_task(self):
        self._test_default_config(PyCondaLiveTask)

    def test_r_conda_env_live_task(self):
        self._test_default_config(RCondaLiveTask)

    def test_mamba_env_live_task(self):
        self._test_default_config(PyMambaLiveTask)

    def test_r_mamba_env_live_task(self):
        self._test_default_config(RMambaLiveTask)

    def _test_default_config(self, task_type: Type[Task]):
        """Test the default env live task config template to be sure it is valid
        """

        # create a csv file
        data = DataFrame({'col1': [0, 1], 'col2': [0, 2]}, index=['a', 'b'])
        temp_dir = Settings.make_temp_dir()
        source = os.path.join(temp_dir, "source.csv")
        data.to_csv(source, index=True)

        tester = TaskRunner(
            task_type=task_type,
            inputs={"source": File(source)},
        )

        outputs = tester.run()

        target: File = outputs["target"]

        self.assertTrue(isinstance(target, File))
        target_data: DataFrame = read_csv(target.path, header=0, index_col=0, sep=',')

        self.assertTrue(target_data.T.equals(data))

        FileHelper.delete_dir(temp_dir)

    def test_live_task_with_exception(self):
        tester = TaskRunner(
            params={
                "code": """
raise Exception('This is not working')
""",
            },
            task_type=PyPipenvLiveTask
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
