# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import asyncio
import unittest

from gws.resource import Resource
from gws.penv.conda import CondaEnvShell
from gws.unittest import GTest

class IPAddressLookup(CondaEnvShell):
    input_specs = {}
    output_specs = {'stdout': (Resource, )}
    _dependencies = ["pyjwt"]
    
    def build_command(self) -> list:
        __cdir__ = os.path.dirname(os.path.realpath(__file__))
        return [
            "python",
            os.path.join(__cdir__, "testdata", "penv", "jwt_encode.py")
        ]

    def gather_outputs(self):
        res = Resource()
        res.data["encoded_string"] = self._stdout
        self.output["stdout"] = res

class TestProcess(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_conda(self):
        GTest.print("Conda")
        proc = IPAddressLookup()
        self.assertFalse(proc.is_installed())

        e = proc.create_experiment(user=GTest.user, study=GTest.study)
        asyncio.run( e.run() )

        result = proc.output["stdout"]
        encoded_string = result.data["encoded_string"]
        self.assertEqual(encoded_string, "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U")
        
        self.assertTrue(proc.is_installed())
        self.assertTrue(proc.is_finished)
        
        proc.uninstall()
        self.assertFalse(proc.is_installed())

        