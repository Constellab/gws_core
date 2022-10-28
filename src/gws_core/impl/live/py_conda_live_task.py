# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ...task.task_decorator import task_decorator
from .base.conda_live_task import CondaLiveTask


@task_decorator(
    "PyCondaLiveTask", human_name="Python live task [conda shell]",
    short_description="Live task to run Python snippets in a conda shell environment. The inputs files are passed to the snippet through the arguments.")
class PyCondaLiveTask(CondaLiveTask):
    """
    This task executes Python snippets on the fly in conda shell environments.

    > **Warning**: It is recommended to use code snippets comming from trusted sources.
    """

    code_file_extension: str = ".py"

    def _format_command(self, code_file_path: str, args: str) -> list:
        return ["python", code_file_path, args]
