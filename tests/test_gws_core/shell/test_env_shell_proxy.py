

import os
from typing import Type
from unittest import TestCase

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import \
    BasicMessageObserver
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.impl.shell.conda_shell_proxy import CondaShellProxy
from gws_core.impl.shell.mamba_shell_proxy import MambaShellProxy
from gws_core.impl.shell.pip_shell_proxy import PipShellProxy
from gws_core.impl.shell.virtual_env.venv_dto import (VEnsStatusDTO,
                                                      VEnvBasicInfoDTO,
                                                      VEnvCreationInfo)
from gws_core.impl.shell.virtual_env.venv_service import VEnvService


# test_env_shell_proxy
class TestEnvShellProxy(TestCase):

    def test_pip_shell_proxy(self):
        pip_env_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                    "penv", "env_jwt_pip.txt")
        self._test_env_shell_proxy(PipShellProxy, 'MyPipTestEnvironment', pip_env_file)

    def test_conda_shell_proxy(self):
        conda_env_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                      "penv", "env_jwt_conda.yml")
        self._test_env_shell_proxy(CondaShellProxy, 'MyCondaTestEnvironment', conda_env_file)

    def test_mamba_shell_proxy(self):
        conda_env_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                      "penv", "env_jwt_conda.yml")
        self._test_env_shell_proxy(MambaShellProxy, 'MyMambaTestEnvironment', conda_env_file)

    def _test_env_shell_proxy(self, shell_proxy_type: Type[BaseEnvShell], env_name: str,
                              env_file_path: str):

        python_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   "penv", "jwt_encode.py")

        # create observer to get print messages
        message_dispatcher = MessageDispatcher(0, 0)
        basic_observer = BasicMessageObserver()
        message_dispatcher.attach(basic_observer)

        shell_proxy: BaseEnvShell = shell_proxy_type(
            env_name, env_file_path, message_dispatcher=message_dispatcher)

        if shell_proxy.env_is_installed():
            shell_proxy.uninstall_env()
        try:

            shell_proxy.install_env()

            self.assertTrue(shell_proxy.env_is_installed())
            self.assertTrue(shell_proxy_type.folder_is_env(shell_proxy.get_env_dir_path()))

            creation_info: VEnvCreationInfo = shell_proxy_type.get_creation_info(shell_proxy.get_env_dir_path())

            self.assertEqual(creation_info.name, env_name)
            self.assertTrue(creation_info.created_at is not None and creation_info.created_at != '')
            self.assertEqual(creation_info.origin_env_config_file_path, env_file_path)

            # Test venv service
            status: VEnsStatusDTO = VEnvService.get_vens_status()

            self.assertTrue(len([x for x in status.envs if x.creation_info.name == env_name]) == 1)
            basic_info: VEnvBasicInfoDTO = [x for x in status.envs if x.creation_info.name == env_name][0]

            self.assertEqual(basic_info.creation_info.name, env_name)
            self.assertEqual(basic_info.folder, shell_proxy.get_env_dir_path())
            self.assertIsNotNone(basic_info.creation_info)
            self.assertEqual(basic_info.creation_info.env_type, shell_proxy.get_env_type())

            venv_info = VEnvService.get_venv_complete_info(basic_info.name)

            self.assertIsNotNone(venv_info.basic_info)
            self.assertTrue(venv_info.env_size > 0)

            # check that the PipFile saved in the venv is the same as the one used to create the venv
            with open(env_file_path, 'r+', encoding='UTF-8') as file:
                config_file_content = file.read()

            self.assertEqual(venv_info.config_file_content, config_file_content)

            # if we try to recreate the venv, it should not be recreated
            self.assertFalse(shell_proxy.install_env())

            # Run a command
            result = shell_proxy.run(f"python {python_file}")
            self.assertEqual(result, 0)
            self.assertTrue(basic_observer.has_message_containing('eyJhb'))

            VEnvService.delete_venv(basic_info.name)
            self.assertFalse(shell_proxy.env_is_installed())

        finally:
            shell_proxy.uninstall_env()
