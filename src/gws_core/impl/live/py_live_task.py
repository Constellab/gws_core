# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import traceback

from gws_core.config.param.code_param.python_code_param import PythonCodeParam
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.live.base.env_live_task import EnvLiveTask
from gws_core.impl.live.helper.live_code_helper import LiveCodeHelper
from gws_core.resource.resource_factory import ResourceFactory

from ...config.config_types import ConfigParams, ConfigSpecs
from ...io.io_spec import InputSpec, OutputSpec
from ...io.io_spec_helper import InputSpecs, OutputSpecs
from ...resource.resource import Resource
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator("PyLiveTask", human_name="Python live task",
                short_description="Live task to run Python snippets directly in the global environment. The input data and parameters are passed in memory to the snippet.")
class PyLiveTask(Task):
    """
    Python live tasks allow to execute any Python code snippets on the fly.

    Live tasks are fast and efficient tools to develop, test, use and share code snippets.

    **Warning**: It is recommended to use code snippets comming from trusted sources.

    Here is the general documentation for live task (including how to use the parameters): https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/getting-started

    Here is the documentation of the live task: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/python-live-task
    """

    input_specs: InputSpecs = {
        'source': InputSpec(Resource, is_optional=True),
    }
    output_specs: OutputSpecs = {
        'target': OutputSpec(Resource, sub_class=True, is_optional=True),
    }
    config_specs: ConfigSpecs = {
        'params': EnvLiveTask.get_list_param_config(),
        'code':
        PythonCodeParam(
            default_value=LiveCodeHelper.get_python_template(),
            human_name="Python code snippet",
            short_description="Python code snippet to run"), }

    working_dir: str = None

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

        # execute the live code
        init_globals = {'self': self, "source": inputs.get('source'),
                        "working_dir": self.working_dir, **globals()}

        try:
            result = LiveCodeHelper.run_python_code(
                code_with_params, init_globals)
        except Exception as err:
            self.log_error_message(
                'Error during the execution of the live task, here is the detail')
            self.log_error_message(traceback.format_exc())
            raise (err)
        result = LiveCodeHelper.run_python_code(code_with_params, init_globals)
        output = result.get("target", None)

        if not isinstance(output, Resource):
            self.log_info_message(
                'The output is not a Resource. Trying to convert it to a Resource...')
            output = ResourceFactory.create_from_object(output)

        return {'target': output}

    def run_after_task(self) -> None:
        FileHelper.delete_dir(self.working_dir)
