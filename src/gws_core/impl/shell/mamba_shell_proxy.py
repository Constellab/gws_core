
# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.impl.shell.conda_shell_proxy import CondaShellProxy


class MambaShellProxy(CondaShellProxy):

    conda_command = "mamba"
