# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...task.task_decorator import task_decorator
from .base.pipenv_live_task import PipenvLiveTask


@task_decorator(
    "PyPipenvLiveTask", human_name="Python live task [pipenv shell]",
    short_description="Live task to run Python snippets in a pipenv shell environment. The inputs files are passed to the snippet through the arguments.")
class PyPipenvLiveTask(PipenvLiveTask):
    """
    This task executes Python snippets on the fly in pipenv shell environments.

    > **Warning**: It is recommended to use code snippets comming from trusted sources.
    """

    code_file_extension: str = ".py"

    def _format_command(self, code_file_path: str, args: str) -> list:
        return ["python", code_file_path, args]
