

from typing import Any, Callable, Dict, Type

import streamlit as st

from gws_core.community.community_front_service import CommunityFrontService
from gws_core.config.config import Config
from gws_core.config.config_params import ConfigParamsDict
from gws_core.core.utils.utils import Utils
from gws_core.resource.resource import Resource
from gws_core.streamlit.components.streamlit_component_loader import \
    StreamlitComponentLoader
from gws_core.streamlit.widgets.streamlit_state import StreamlitState
from gws_core.task.task import Task
from gws_core.task.task_io import TaskOutputs
from gws_core.task.task_runner import TaskRunner


class StreamlitTaskRunner():
    """Class to generate a form to configure a task in streamlit.
    The task is then automatically run when the form is submitted.
    The task is run in a separate thread, so the streamlit app is not blocked.

    To use this component, you need to use a Streamlit app that requires authentication.
    """

    task_type: Type[Task]

    _streamlit_component_loader = StreamlitComponentLoader("process-config")

    def __init__(self, task_type: Type[Task]):

        if not Utils.issubclass(task_type, Task):
            raise ValueError("task_type must be a subclass of Task")
        self.task_type = task_type

    def generate_form(self, default_config_values: ConfigParamsDict = None,
                      inputs: Dict[str, Resource] = None,
                      key: str = 'task-runner') -> TaskOutputs:
        """Generate the form from the values
        """
        return self._generate_component_and_call_run(key, default_config_values, inputs)

    def generate_form_dialog(self, default_config_values: ConfigParamsDict = None,
                             inputs: Dict[str, Resource] = None,
                             on_run_success: Callable[[TaskOutputs], None] = None,
                             key: str = 'task-runner') -> None:
        """Generate the form from the values
        """

        if self.task_type.config_specs.has_visible_config_specs():
            self._open_dialog(key, default_config_values, inputs, on_run_success)
        else:
            # if the task doesn't have config, call it directly
            result = self._run_task(default_config_values, inputs)
            if on_run_success is not None:
                on_run_success(result)
            st.rerun()

    @st.dialog("Configure the process", width='large')
    def _open_dialog(self,
                     key: str,
                     config_values: ConfigParamsDict = None,
                     inputs: Dict[str, Resource] = None,
                     on_run_success: Callable[[TaskOutputs], None] = None) -> None:
        """Open the dialog, on form submit, the value will be stored in the session state and the page will be rerun.
        Call get_dialog_value to get the value
        """
        result = self._generate_component_and_call_run(key, config_values, inputs)

        if result is not None:
            if on_run_success is not None:
                on_run_success(result)
            st.rerun()

    def _generate_component_and_call_run(self,
                                         key: str,
                                         default_config_values: ConfigParamsDict = None,
                                         inputs: Dict[str, Resource] = None) -> TaskOutputs | None:
        """Generate the form from the values, and run the task
        """
        component_value = self._generate_component(key, default_config_values)

        if component_value is None:
            return None

        return self._run_task(component_value, inputs)

    def _generate_component(self, key: str, default_config_values: ConfigParamsDict = None) -> ConfigParamsDict | None:

        config = Config()
        config.set_specs(self.task_type.config_specs)

        if default_config_values is not None:
            config.set_values(default_config_values)

        data = {
            'typing_name': self.task_type.get_typing_name(),
            'specs': self._get_task_specs_json(config),
            'values': default_config_values,
            'process_description': self.task_type.get_short_description(),
            'doc_url': CommunityFrontService.get_typing_doc_url(self.task_type.get_typing_name()),
        }

        component_value = self._streamlit_component_loader.call_component(
            data, key=key,
            authentication_info=StreamlitState.get_and_check_app_authentication_for_component('StreamlitTaskRunner'))

        if component_value is None:
            return None

        config.set_values(component_value)
        return config.get_and_check_values()

    def _get_task_specs_json(self, config: Config) -> Dict[str, Any]:
        specs = config.to_specs_dto()

        specs_json: dict = {}
        for key, spec in specs.items():
            specs_json[key] = spec.to_json_dict()

        return specs_json

    def _run_task(self, config_values: ConfigParamsDict = None,
                  inputs: Dict[str, Resource] = None) -> TaskOutputs:
        # run the task
        task_runner = TaskRunner(self.task_type, params=config_values, inputs=inputs)

        try:
            return task_runner.run()
        except Exception as e:
            st.error(f"Error during the execution of the task : {e}")
            with st.popover('View details'):
                st.exception(e)
            st.stop()
