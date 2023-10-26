# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.impl.live.r_conda_live_task import RCondaLiveTask
from gws_core.impl.shell.mamba_shell_proxy import MambaShellProxy

from ...task.task_decorator import task_decorator


@task_decorator(
    "RMambaLiveTask", human_name="R mamba env live task",
    short_description="Live task to run R snippets in mamba a shell environment.")
class RMambaLiveTask(RCondaLiveTask):
    """
    Mamba-based R live tasks allow to execute R snippets on the fly in isolated mamba environments.

    Live tasks are fast and efficient tools to develop, test, use and share code snippets.

    **Warning**: It is recommended to use code snippets comming from trusted sources.

    Here is the general documentation for live task (including how to use the parameters): https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/getting-started

    Here is the documentation of the live task: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/env-live-task
    """

    def _create_shell_proxy(self, env: str) -> MambaShellProxy:
        return MambaShellProxy.from_env_str(env, message_dispatcher=self.message_dispatcher)
