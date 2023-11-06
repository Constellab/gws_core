
# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing_extensions import Literal

from gws_core.impl.shell.conda_shell_proxy import CondaShellProxy


class MambaShellProxy(CondaShellProxy):

    conda_command = "mamba"

    @classmethod
    def get_env_type(cls) -> Literal['conda', 'mamba', 'pip']:
        return 'mamba'
