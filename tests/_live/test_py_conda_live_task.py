# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BaseTestCase, File, PyCondaLiveTask, ResourceSet, Table,
                      TaskRunner)
from pandas import DataFrame


class TestPyCondaLiveTask(BaseTestCase):

    async def test_live_task_shell(self):
        file_set = ResourceSet()
        file = File(path="./foo/bar")
        file.name = "my_file"
        file_set.add_resource(file)

        tester = TaskRunner(
            params={
                "code": """
import jwt
import sys
# parse arguments
for k,val in enumerate(sys.argv):
    if val == "--data":
        data_path = sys.argv[k+1]
    elif val == "--result":
        result_path = sys.argv[k+1]
print(str(sys.argv))
encoded_jwt = jwt.encode({"some": "payload"}, "secret", algorithm="HS256")
print(encoded_jwt, end="")
with open(result_path, "w", encoding="utf-8") as fp:
    fp.write(encoded_jwt)
with open("out2.txt", "w", encoding="utf-8") as fp:
    fp.write(data_path)
""",
                "args": "--data {input:my_file} --result ./out1.txt",
                "env": """
name: .venv3
channels:
- conda-forge
dependencies:
- python=3.8
- pyjwt""",
                "output_file_paths": ["./out1.txt", "out2.txt"]
            },
            inputs={"source": file_set},
            task_type=PyCondaLiveTask
        )

        outputs = await tester.run()
        target = outputs["target"]
        self.assertTrue(isinstance(target, ResourceSet))

        resources = target.get_resources()

        file1 = resources["./out1.txt"]
        self.assertTrue(isinstance(file1, File))
        self.assertEqual(
            file1.read().strip(),
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzb21lIjoicGF5bG9hZCJ9.4twFt5NiznN84AWoo1d7KO1T_yoc0Z6XOpOVswacPZg")

        # self.assertEqual(
        #     file1.read().strip(),
        #     "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U")

        file2 = resources["out2.txt"]
        self.assertTrue(isinstance(file2, File))
        self.assertEqual(
            file2.read().strip(),
            "./foo/bar")
