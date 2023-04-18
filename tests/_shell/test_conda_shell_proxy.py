# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os
from unittest import TestCase

from gws_core.impl.shell.base_env_shell import VEnvCreationInfo
from gws_core.impl.shell.conda_shell_proxy import CondaShellProxy
from gws_core.impl.shell.venv_service import (VEnsStatus, VEnvBasicInfo,
                                              VEnvService)


# test_conda_shell_proxy
class TestCondaShellProxy(TestCase):

    def test_conda_shell_proxy(self):

        conda_env_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                      "penv", "env_jwt_conda.yml")
        conda_proxy = CondaShellProxy('MyCondaTestEnvironment', conda_env_file)
        try:

            conda_proxy.install_env()

            self.assertTrue(conda_proxy.env_is_installed())
            self.assertTrue(CondaShellProxy.folder_is_env(conda_proxy.get_env_dir_path()))

            creation_info: VEnvCreationInfo = CondaShellProxy.get_creation_info(conda_proxy.get_env_dir_path())

            self.assertEqual(creation_info['name'], 'MyCondaTestEnvironment')
            self.assertTrue(creation_info['created_at'] is not None and creation_info['created_at'] != '')
            self.assertEqual(creation_info['origin_env_config_file_path'], conda_env_file)

            # Test venv service
            status: VEnsStatus = VEnvService.get_vens_status()

            self.assertTrue(len([x for x in status['conda_envs'] if x['name'] == 'MyCondaTestEnvironment']) == 1)
            basic_info: VEnvBasicInfo = [x for x in status['conda_envs'] if x['name'] == 'MyCondaTestEnvironment'][0]

            self.assertEqual(basic_info['name'], 'MyCondaTestEnvironment')
            self.assertEqual(basic_info['folder'], conda_proxy.get_env_dir_path())
            self.assertEqual(basic_info['type'], 'conda')
            self.assertIsNotNone(basic_info['creation_info'], 'MyCondaTestEnvironment')

            venv_info = VEnvService.get_venv_complete_info('MyCondaTestEnvironment')

            self.assertIsNotNone(venv_info['basic_info'])
            self.assertTrue(venv_info['env_size'] > 0)

            # check that the environment.yml file saved in the venv
            # is the same as the one used to create the venv
            with open(conda_env_file, 'r+', encoding='UTF-8') as fp:
                config_file_content = fp.read()

            self.assertEqual(venv_info['config_file_content'], config_file_content)

            # if we try to recreate the venv, it should not be recreated
            self.assertFalse(conda_proxy.install_env())

            VEnvService.delete_venv('MyCondaTestEnvironment')
            self.assertFalse(conda_proxy.env_is_installed())

        except:
            conda_proxy.uninstall_env()
