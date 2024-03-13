

from typing import List

from gws_core.config.param.code_param.python_code_param import PythonCodeParam
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.live.base.env_live_task import EnvLiveTask
from gws_core.impl.live.helper.live_code_helper import LiveCodeHelper
from gws_core.io.dynamic_io import DynamicInputs, DynamicOutputs
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource_set.resource_list import ResourceList

from ...config.config_params import ConfigParams
from ...config.config_types import ConfigParamsDict, ConfigSpecs
from ...io.io_specs import InputSpecs, OutputSpecs
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator("PyLiveTask", human_name="Python live task",
                short_description="Live task to run Python snippets directly in the global environment. The input data and parameters are passed in memory to the snippet.",
                style=TypingStyle.material_icon("code"))
class PyLiveTask(Task):
    """
    Python live tasks allow to execute any Python code snippets on the fly.

    Live tasks are fast and efficient tools to develop, test, use and share code snippets.

    **Warning**: It is recommended to use code snippets comming from trusted sources.

    Here is the general documentation for live task (including how to use the parameters): https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/getting-started

    Here is the documentation of the live task: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/python-live-task
    """

    input_specs: InputSpecs = DynamicInputs()
    output_specs: OutputSpecs = DynamicOutputs()
    config_specs: ConfigSpecs = {
        'params': EnvLiveTask.get_list_param_config(),
        'code':
        PythonCodeParam(
            default_value=LiveCodeHelper.get_python_template(),
            human_name="Python code snippet",
            short_description="Python code snippet to run"), }

    working_dir: str = None

    CONFIG_PARAMS_NAME = 'params'
    CONFIG_CODE_NAME = 'code'

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        code: str = params.get_value('code')
        params = params.get_value('params')

        # convert param to string and leave empty if no params so it does not offset the
        # line number of the code
        str_params = "\n".join(params)
        if len(params) > 0:
            str_params = str_params + "\n"

        # add the params to the code
        code_with_params = f"{str_params}{code}"

        self.working_dir = Settings.make_temp_dir()

        resource_list: ResourceList = inputs.get('source')

        # execute the live code
        init_globals = {'self': self, 'sources': resource_list.get_resources(),
                        "working_dir": self.working_dir, **globals()}

        result = LiveCodeHelper.run_python_code(code_with_params, init_globals)

        targets = result.get("targets", None)

        if targets is None:
            raise Exception("The 'targets' variable is None")

        return {'target': ResourceList(targets)}

    def run_after_task(self) -> None:
        FileHelper.delete_dir(self.working_dir)

    @classmethod
    def build_config_params_dict(cls, code: str, params: List[str]) -> ConfigParamsDict:
        return {'code': code, "params": params}
