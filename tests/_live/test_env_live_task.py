# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from unittest import TestCase

from gws_core import File, PyCondaLiveTask, TaskRunner
from gws_core.core.classes.observer.message_level import MessageLevel
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.folder import Folder
from gws_core.impl.live.py_pipenv_live_task import PyPipenvLiveTask
from gws_core.resource.resource_set.resource_set import ResourceSet


# test_env_live_task
class TestEnvLiveTask(TestCase):

    jwt_encoder_code = """
import jwt
import os
# read source_path file
with open(source_path, "r", encoding="utf-8") as fp:
    data = fp.read()

encoded_jwt = jwt.encode({"text": data}, "secret", algorithm="HS256")

# write result
result_path = os.path.join(target_folder, "result.txt")
with open(result_path, "w", encoding="utf-8") as fp:
    fp.write(encoded_jwt)
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
        self.assertEqual(
            target.read().strip(),
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0ZXh0IjoiSGVsbG8gd29ybGQifQ.MqI-2MrQhflRwSHn910mOBfL3K8Kf39DXZaMmnmPGGg")

    def test_resource_set_live_task(self):
        """
        Test a live task that takes multiple files as input and return a resource set

        Test a code that concatenate two files into a single file.
        It duplicate the result in 2 files"""
        file = self._create_file()
        file_2 = self._create_file(
            file_name='source_2.txt', content="Micheal !")

        resource_set = ResourceSet()
        resource_set.add_resource(file, file.get_default_name())
        resource_set.add_resource(file_2, file_2.get_default_name())

        tester = TaskRunner(
            params={
                # CODE
                "code":
                """
import os

# loop over source_path files and concatenate them into a single string
data = text_start
for file in os.listdir(source_path):
    with open(os.path.join(source_path, file), "r", encoding="utf-8") as fp:
        data += fp.read()

# write result
result_path = os.path.join(target_folder, "result.txt")
with open(result_path, "w", encoding="utf-8") as fp:
    fp.write(data)

# create subfolder 'subfolder'
subfolder = os.path.join(target_folder, "subfolder")
os.mkdir(subfolder)
result_path_2 = os.path.join(subfolder, "result_2.txt")
with open(result_path_2, "w", encoding="utf-8") as fp:
    fp.write("Hello world")
                """,
                # SET ENVIRONMENT
                "env": self.pip_env_str,
                "params": ["text_start='Start'"]
            },
            inputs={"source": resource_set},
            task_type=PyPipenvLiveTask
        )

        outputs = tester.run()
        target: ResourceSet = outputs["target"]

        self.assertTrue(isinstance(target, ResourceSet))
        self.assertEqual(len(target.get_resources()), 2)

        result_1: File = target.get_resource("result.txt")
        result_2: Folder = target.get_resource("subfolder")

        self.assertTrue(isinstance(result_1, File))
        self.assertTrue(isinstance(result_2, Folder))

        self.assertTrue('Micheal !' in result_1.read().strip())
        self.assertTrue('Hello world' in result_1.read().strip())
        # check that the param was correctly set
        self.assertTrue('Start' in result_1.read().strip())

        tester.run_after_task()

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
