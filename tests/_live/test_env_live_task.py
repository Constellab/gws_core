# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from unittest import TestCase

from gws_core import File, PyCondaLiveTask, TaskRunner
from gws_core.core.classes.observer.message_level import MessageLevel
from gws_core.core.utils.settings import Settings
from gws_core.impl.live.py_pipenv_live_task import PyPipenvLiveTask


# test_env_live_task
class TestEnvLiveTask(TestCase):

    jwt_encoder_code = """
import jwt
import os
# read source_paths file
with open(source_paths[0], "r", encoding="utf-8") as fp:
    data = fp.read()

encoded_jwt = jwt.encode({"text": data}, "secret", algorithm="HS256")

# write result
result_path = "result.txt"
with open(result_path, "w", encoding="utf-8") as fp:
    fp.write(encoded_jwt)
target_paths.append(result_path)
"""

    conda_env_str = """
name: .venv3
channels:
- conda-forge
dependencies:
- python=3.8
- pyjwt==2.3.0"""

    pip_env_str = """
[[source]]
url = 'https://pypi.python.org/simple'
verify_ssl = true
name = 'pypi'

[requires]
python_version = '3.8'

[packages]
pyjwt = '==2.3.0'"""

    def test_conda_env_live_task(self):

        # create file resource
        file = self._create_file()

        tester = TaskRunner(
            params={
                "code": self.jwt_encoder_code,
                "env": self.conda_env_str,
            },
            inputs={"source": file},
            task_type=PyCondaLiveTask
        )

        outputs = tester.run()
        target: File = outputs["target"]

        self._check_output(target)
        tester.run_after_task()

    def test_pip_env_live_task(self):

        # create file resource
        file = self._create_file()

        tester = TaskRunner(
            params={
                "code": self.jwt_encoder_code,
                "env": self.pip_env_str,
            },
            inputs={"source": file},
            task_type=PyPipenvLiveTask
        )

        outputs = tester.run()
        target: File = outputs["target"]

        self._check_output(target)
        tester.run_after_task()

    def _create_file(self, file_name: str = 'source.txt', content: str = "Hello world") -> File:
        temp_dir = Settings.make_temp_dir()
        source = os.path.join(temp_dir, file_name)
        # set 'Hello world' in a file
        with open(source, "w", encoding="utf-8") as file_path:
            file_path.write(content)

        # create file resource
        return File(source)

    def _check_output(self, target: File) -> None:

        self.assertTrue(isinstance(target, File))
        value = target.read().strip()
        self.assertIsNotNone(value)
        self.assertTrue(len(value) > 0)

    def test_live_task_with_exception(self):
        tester = TaskRunner(
            params={
                "code": """
raise Exception('This is not working')
""",
                "env": self.pip_env_str,
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
