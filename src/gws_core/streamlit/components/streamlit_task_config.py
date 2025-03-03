

from typing import Any, Dict, Type

import streamlit as st

from gws_core.config.config import Config
from gws_core.config.config_types import ConfigParamsDict
from gws_core.core.utils.utils import Utils
from gws_core.streamlit.components.streamlit_component_loader import \
    StreamlitComponentLoader
from gws_core.task.task import Task


class StreamlitTaskConfig():

    task_type: Type[Task]
    config: Config
    key: str

    _streamlit_component_loader = StreamlitComponentLoader(
        "process-config",
        version="dc_process_config_1.0.0",
        is_released=False)

    def __init__(self, task_type: Type[Task], key: str = 'process-config'):

        if not Utils.issubclass(task_type, Task):
            raise ValueError("task_type must be a subclass of Task")
        self.task_type = task_type
        self.key = key
        self.config = Config()
        self.config.set_specs(self.task_type.config_specs)

    def generate_form(self, config_values: ConfigParamsDict = None) -> Dict[str, Any]:
        """Generate the form from the values
        """
        return self._generate_component(config_values)

    def generate_form_dialog(self, config_values: ConfigParamsDict = None) -> None:
        """Generate the form from the values
        """
        self._open_dialog(config_values)

    @st.dialog("Configure the process", width='large')
    def _open_dialog(self, config_values: ConfigParamsDict = None) -> None:
        """Open the dialog, on form submit, the value will be stored in the session state and the page will be rerun.
        Call get_dialog_value to get the value
        """
        component_value = self._generate_component(config_values)

        if component_value is not None:
            st.session_state[self.key] = component_value
            st.rerun()

    def _generate_component(self, config_values: ConfigParamsDict = None) -> ConfigParamsDict:
        if config_values is not None:
            self.config.set_values(config_values)

        component_value = self._streamlit_component_loader.get_function()(
            specs=self._get_task_specs_json(),
            values=self.config.get_and_check_values(),
            processDescription=self.task_type.get_short_description())

        if component_value is not None:
            self.config.set_values(component_value)

        return component_value

    def _get_task_specs_json(self) -> Dict[str, Any]:
        specs = self.config.to_specs_dto()

        specs_json: dict = {}
        for key, spec in specs.items():
            specs_json[key] = spec.to_json_dict()

        return specs_json

    def get_dialog_value(self) -> Dict[str, Any] | None:
        values = st.session_state.get(self.key)
        if values is None:
            return None
        self.config.set_values(values)
        return self.config.get_values()
