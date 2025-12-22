from typing import Literal

from gws_core.impl.shell.conda_shell_proxy import CondaShellProxy
from gws_core.model.typing_register_decorator import typing_registrator


@typing_registrator(unique_name="MambaShellProxy", object_type="MODEL", hide=True)
class MambaShellProxy(CondaShellProxy):
    """Shell proxy for managing Mamba virtual environments.

    Mamba is a faster alternative to Conda for managing Python environments and packages.
    This class extends CondaShellProxy but uses the `mamba` command instead of `conda`
    for environment installation and management operations.

    All other functionality is inherited from CondaShellProxy, including environment
    activation and command execution.
    """
    conda_command = "mamba"

    @classmethod
    def get_env_type(cls) -> Literal["conda", "mamba", "pip"]:
        """Get the environment type identifier.

        :return: The string "mamba"
        :rtype: Literal["conda", "mamba", "pip"]
        """
        return "mamba"
