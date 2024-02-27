# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.code_param.python_code_param import PythonCodeParam
from gws_core.impl.file.fs_node import FSNode
from gws_core.impl.live.helper.live_code_helper import LiveCodeHelper
from gws_core.io.dynamic_io import DynamicInputs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.streamlit.streamlit_resource import StreamlitResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator("StreamlitLiveTask", human_name="Streamlite live task", icon="code")
class StreamlitLiveTask(Task):
    """
    Live task to generate a streamlit app dashboard.

    **Warning**: It is recommended to use code snippets comming from trusted sources.

    Here is the general documentation for live task (including how to use the parameters): https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/getting-started

    Here is the documentation of the streamlit live task: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/streamlit-live-task

    More information about streamlit: https://streamlit.io
    """

    input_specs: InputSpecs = DynamicInputs(
        additionnal_port_spec=InputSpec(FSNode, human_name="File or folder", is_optional=True))
    output_specs: OutputSpecs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource, human_name="Streamlit app")
    })
    config_specs: ConfigSpecs = {
        'code':
        PythonCodeParam(
            default_value=LiveCodeHelper.get_streamlit_template(),
            human_name="Streamlit app code",
            short_description="Code of the streamlit app to run"), }

    CONFIG_PARAMS_NAME = 'params'
    CONFIG_CODE_NAME = 'code'

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        code: str = params.get_value('code')

        streamlit_resource = StreamlitResource(code)

        resource_list: ResourceList = inputs.get('source')
        i = 0
        for resource in resource_list.get_resources_as_set():
            streamlit_resource.add_resource(resource, unique_name=f"resource_{i}",
                                            create_new_resource=False)

        return {'streamlit_app': streamlit_resource}
