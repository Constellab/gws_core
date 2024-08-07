
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigParamsDict, ConfigSpecs
from gws_core.config.param.code_param.python_code_param import PythonCodeParam
from gws_core.impl.live.helper.live_code_helper import LiveCodeHelper
from gws_core.io.dynamic_io import DynamicInputs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingIconType
from gws_core.resource.resource import Resource
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.streamlit.streamlit_resource import StreamlitResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator("StreamlitLiveTask", human_name="Streamlit live task",
                short_description="Live task to generate a streamlit app dashboard",
                style=StreamlitResource.copy_style(
                    icon_technical_name='code', icon_type=TypingIconType.MATERIAL_ICON))
class StreamlitLiveTask(Task):
    """
    Live task to generate a streamlit app dashboard.

    **Warning**: It is recommended to use code snippets comming from trusted sources.

    Here is the general documentation for live task (including how to use the parameters): https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/getting-started/69820653-52e0-41ba-a5f3-4d9d54561779

    Here is the documentation of the live task: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/env-live-task/c6acb3c3-2a7c-44cd-8fb2-ea1beccdbdcc

    More information about streamlit: https://streamlit.io
    """

    input_specs: InputSpecs = DynamicInputs(
        additionnal_port_spec=InputSpec(Resource, human_name="Resource", is_optional=True))
    output_specs: OutputSpecs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource, human_name="Streamlit app")
    })
    config_specs: ConfigSpecs = {
        'code':
        PythonCodeParam(
            default_value=LiveCodeHelper.get_streamlit_template(),
            human_name="Streamlit app code",
            short_description="Code of the streamlit app to run"), }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        code: str = params.get_value('code')

        # build the streamlit resource with the code and the resources
        streamlit_resource = StreamlitResource(code)
        resource_list: ResourceList = inputs.get('source')
        for resource in resource_list.get_resources():
            if resource:
                streamlit_resource.add_resource(resource, create_new_resource=False)

        return {'streamlit_app': streamlit_resource}

    @classmethod
    def build_config_params_dict(cls, code: str) -> ConfigParamsDict:
        return {'code': code}
