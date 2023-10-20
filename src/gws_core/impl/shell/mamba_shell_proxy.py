from gws_core.impl.shell.conda_shell_proxy import CondaShellProxy


class MambaShellProxy(CondaShellProxy):

    conda_command = "mamba"
