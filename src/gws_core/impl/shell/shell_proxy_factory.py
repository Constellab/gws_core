from gws_core.core.utils.utils import Utils
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.impl.shell.shell_proxy import ShellProxy, ShellProxyDTO
from gws_core.model.typing_manager import TypingManager


class ShellProxyFactory:
    """Factory class for creating ShellProxy instances from DTOs.

    This factory handles the deserialization of ShellProxy objects, including
    both basic ShellProxy instances and environment-based shells (BaseEnvShell subclasses).
    """

    @classmethod
    def build_shell_proxy(cls, shell_proxy_dto: ShellProxyDTO) -> ShellProxy:
        """Build a ShellProxy instance from a data transfer object.

        Creates the appropriate ShellProxy subclass based on the typing_name in the DTO.
        For BaseEnvShell subclasses, uses the env_code to configure the environment.

        :param shell_proxy_dto: DTO containing the shell proxy configuration
        :type shell_proxy_dto: ShellProxyDTO
        :return: Instantiated ShellProxy of the appropriate type
        :rtype: ShellProxy
        :raises TypeError: If the typing_name does not correspond to a ShellProxy subclass
        :raises ValueError: If env_code is missing for BaseEnvShell types
        """
        shell_type = TypingManager.get_type_from_name(shell_proxy_dto.typing_name)

        if shell_type is None:
            raise TypeError(f"Unknown shell_proxy_typing_name: {shell_proxy_dto.typing_name}")

        if not Utils.issubclass(shell_type, ShellProxy):
            raise TypeError(
                f"shell_proxy_typing_name must be a subclass of ShellProxy, not {shell_type}"
            )

        if Utils.issubclass(shell_type, BaseEnvShell):
            if not shell_proxy_dto.env_code:
                raise ValueError(
                    f"env_core must be provided for env shell_proxy_typing_name {shell_proxy_dto.typing_name}"
                )

            base_env_type: type[BaseEnvShell] = shell_type
            return base_env_type.from_env_str(shell_proxy_dto.env_code)

        return shell_type()
