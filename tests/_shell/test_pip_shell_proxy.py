# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os
from unittest import TestCase

from gws_core.impl.shell.base_env_shell import VEnvCreationInfo
from gws_core.impl.shell.pip_shell_proxy import PipShellProxy
from gws_core.impl.shell.venv_service import (VEnsStatus, VEnvBasicInfo,
                                              VEnvService)


# test_pip_shell_proxy
class TestPipShellProxy(TestCase):

    def test_pip_shell_proxy(self):

        pip_env_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                    "penv", "env_jwt_pip.txt")
        pip_proxy = PipShellProxy('MyPipTestEnvironment', pip_env_file)
        try:

            pip_proxy.install_env()

            self.assertTrue(pip_proxy.env_is_installed())
            self.assertTrue(PipShellProxy.folder_is_env(pip_proxy.get_env_dir_path()))

            creation_info: VEnvCreationInfo = PipShellProxy.get_creation_info(pip_proxy.get_env_dir_path())

            self.assertEqual(creation_info['name'], 'MyPipTestEnvironment')
            self.assertTrue(creation_info['created_at'] is not None and creation_info['created_at'] != '')
            self.assertEqual(creation_info['origin_env_config_file_path'], pip_env_file)

            # Test venv service
            status: VEnsStatus = VEnvService.get_vens_status()

            self.assertTrue(len([x for x in status['pip_envs'] if x['name'] == 'MyPipTestEnvironment']) == 1)
            basic_info: VEnvBasicInfo = [x for x in status['pip_envs'] if x['name'] == 'MyPipTestEnvironment'][0]

            self.assertEqual(basic_info['name'], 'MyPipTestEnvironment')
            self.assertEqual(basic_info['folder'], pip_proxy.get_env_dir_path())
            self.assertEqual(basic_info['type'], 'pip')
            self.assertIsNotNone(basic_info['creation_info'])

            venv_info = VEnvService.get_venv_complete_info('MyPipTestEnvironment')

            self.assertIsNotNone(venv_info['basic_info'])
            self.assertTrue(venv_info['env_size'] > 0)

            # check that the PipFile saved in the venv is the same as the one used to create the venv
            with open(pip_env_file, 'r+', encoding='UTF-8') as fp:
                config_file_content = fp.read()

            self.assertEqual(venv_info['config_file_content'], config_file_content)

            # if we try to recreate the venv, it should not be recreated
            self.assertFalse(pip_proxy.install_env())

            VEnvService.delete_venv('MyPipTestEnvironment')
            self.assertFalse(pip_proxy.env_is_installed())

        except:
            pip_proxy.uninstall_env()
