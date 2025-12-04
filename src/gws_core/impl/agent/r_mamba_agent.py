from gws_core.impl.agent.r_conda_agent import RCondaAgent
from gws_core.impl.shell.mamba_shell_proxy import MambaShellProxy
from gws_core.model.typing_style import TypingStyle

from ...task.task_decorator import task_decorator


@task_decorator(
    "RMambaAgent",
    human_name="R mamba env agent",
    short_description="Agent to run R snippets in mamba a shell environment.",
    style=TypingStyle.material_icon("agent"),
)
class RMambaAgent(RCondaAgent):
    """
    Mamba-based R agents allow to execute R snippets on the fly in isolated mamba environments.

    Agents are fast and efficient tools to develop, test, use and share code snippets.

    **Warning**: It is recommended to use code snippets comming from trusted sources.

    Here is the general documentation for agent: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/agent/getting-started/69820653-52e0-41ba-a5f3-4d9d54561779

    Here is the documentation of the agent: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/agent/env-agent/c6acb3c3-2a7c-44cd-8fb2-ea1beccdbdcc
    """

    def _create_shell_proxy(self, env: str) -> MambaShellProxy:
        return MambaShellProxy.from_env_str(env, message_dispatcher=self.message_dispatcher)
