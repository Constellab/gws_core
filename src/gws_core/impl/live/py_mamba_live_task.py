# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.impl.live.py_conda_live_task import PyCondaLiveTask
from gws_core.impl.shell.mamba_shell_proxy import MambaShellProxy
from gws_core.model.typing_style import TypingStyle

from ...task.task_decorator import task_decorator


@task_decorator(
    "PyMambaLiveTask", human_name="Mamba env live task",
    short_description="Live task to run Python snippets in a mamba shell environment.",
    style=TypingStyle.material_icon("code"))
class PyMambaLiveTask(PyCondaLiveTask):
    """
    Mamba-based Python live tasks allow to execute Python snippets on the fly in isolated conda environments.

    Live tasks are fast and efficient tools to develop, test, use and share code snippets.

    **Warning**: It is recommended to use code snippets comming from trusted sources.

    Here is the general documentation for live task (including how to use the parameters): https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/getting-started

    Here is the documentation of the live task: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/env-live-task
    """

    def _create_shell_proxy(self, env: str) -> MambaShellProxy:
        return MambaShellProxy.from_env_str(env, message_dispatcher=self.message_dispatcher)
