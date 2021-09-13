# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ..config.config_types import ConfigParams
from ..task.task import Task
from ..task.task_io import TaskInputs, TaskOutputs


class TaskTester():

    _task: Task
    _params: ConfigParams
    _inputs: TaskInputs
    _outputs: TaskOutputs

    def __init__(self, task: Task, params: ConfigParams, inputs: TaskInputs):
        self._params = params
        self._inputs = inputs
        self._task = task

    async def run(self) -> TaskOutputs:
        # TODO: check here params, inputs ...
        self._outputs = await self._task.run(self._params, self._inputs)
        return self._outputs
