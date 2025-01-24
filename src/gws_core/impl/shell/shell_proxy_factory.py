

from typing import Type

from gws_core.core.utils.utils import Utils
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.impl.shell.shell_proxy import ShellProxy, ShellProxyDTO
from gws_core.model.typing_manager import TypingManager


class ShellProxyFactory():

    @classmethod
    def build_shell_proxy(cls, shell_proxy_dto: ShellProxyDTO) -> ShellProxy:

        shell_type: Type = TypingManager.get_type_from_name(shell_proxy_dto.typing_name)

        if not Utils.issubclass(shell_type, ShellProxy):
            raise TypeError(f"shell_proxy_typing_name must be a subclass of ShellProxy, not {shell_type}")

        if Utils.issubclass(shell_type, BaseEnvShell):
            if not shell_proxy_dto.env_code:
                raise ValueError(
                    f"env_core must be provided for env shell_proxy_typing_name {shell_proxy_dto.typing_name}")

            base_env_type: Type[BaseEnvShell] = shell_type
            return base_env_type.from_env_str(shell_proxy_dto.env_code)

        return shell_type()
