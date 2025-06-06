

from typing_extensions import Literal

from gws_core.impl.shell.conda_shell_proxy import CondaShellProxy
from gws_core.model.typing_register_decorator import typing_registrator


@typing_registrator(unique_name="MambaShellProxy", object_type="MODEL", hide=True)
class MambaShellProxy(CondaShellProxy):

    conda_command = "mamba"

    @classmethod
    def get_env_type(cls) -> Literal['conda', 'mamba', 'pip']:
        return 'mamba'
