import os

import streamlit as st
from gws_core import File, FileHelper, Settings, Table, TableImporter, TaskOutputs
from gws_streamlit_main import StreamlitTaskRunner

from ..components.example_tabs_component import example_tabs
from ..components.page_layout_component import page_layout


def render_processes_page():
    def page_content():
        _render_task_config_form()
        _render_task_config_form_in_dialog()
        _render_task_runner()

    page_layout(
        title="Processes",
        description="This page contains a showcase for streamlit component to interact with tasks and protocols.",
        content_function=page_content,
    )


def _render_task_config_form():
    def example_demo():
        if "config_data" not in st.session_state:
            st.session_state["config_data"] = None

        form_config = StreamlitTaskRunner(TableImporter)
        form_config.generate_config_form_without_run(
            session_state_key="config_data",
            default_config_values=TableImporter.config_specs.get_default_values(),
            is_default_config_valid=TableImporter.config_specs.mandatory_values_are_set(
                TableImporter.config_specs.get_default_values()
            ),
        )

        st.write(f"Task config : {st.session_state['config_data']}")

    code = """import streamlit as st
from gws_core import TableImporter
from gws_streamlit_main import StreamlitTaskRunner

if "config_data" not in st.session_state:
    st.session_state["config_data"] = None

form_config = StreamlitTaskRunner(TableImporter)
form_config.generate_config_form_without_run(
    session_state_key="config_data",
    default_config_values=TableImporter.config_specs.get_default_values(),
    is_default_config_valid=TableImporter.config_specs.mandatory_values_are_set(
        TableImporter.config_specs.get_default_values()))

st.write(f"Task config : {st.session_state['config_data']}")"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Task configuration form",
        description="Generate a configuration form for a task without running it.",
        doc_func=StreamlitTaskRunner.generate_config_form_without_run,
    )


def _render_task_config_form_in_dialog():
    def example_demo():
        if "config_data_dialog" not in st.session_state:
            st.session_state["config_data_dialog"] = None

        @st.dialog("Task Configuration")
        def dialog():
            form_config = StreamlitTaskRunner(TableImporter)
            form_config.generate_config_form_without_run(
                session_state_key="config_data_dialog",
                default_config_values=TableImporter.config_specs.get_default_values(),
                is_default_config_valid=TableImporter.config_specs.mandatory_values_are_set(
                    TableImporter.config_specs.get_default_values()
                ),
                key="config-task-form-dialog",
            )

            if st.button("Save"):
                st.rerun()

            st.write(f"Task config : {st.session_state['config_data_dialog']}")

        if st.button("Open Config form dialog"):
            dialog()

        st.write(f"Task config : {st.session_state['config_data_dialog']}")

    code = """import streamlit as st
from gws_core import TableImporter
from gws_streamlit_main import StreamlitTaskRunner

if "config_data_dialog" not in st.session_state:
    st.session_state["config_data_dialog"] = None

@st.dialog("Task Configuration")
def dialog():
    form_config = StreamlitTaskRunner(TableImporter)
    form_config.generate_config_form_without_run(
        session_state_key="config_data_dialog",
        default_config_values=TableImporter.config_specs.get_default_values(),
        is_default_config_valid=TableImporter.config_specs.mandatory_values_are_set(
            TableImporter.config_specs.get_default_values()),
        key="config-task-form-dialog")

    if st.button("Save"):
        st.rerun()

    st.write(f"Task config : {st.session_state['config_data_dialog']}")

if st.button("Open Config form dialog"):
    dialog()

st.write(f"Task config : {st.session_state['config_data_dialog']}")"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Task configuration form in dialog",
        description="Display a task configuration form inside a dialog.",
        doc_func=StreamlitTaskRunner.generate_config_form_without_run,
    )


def _render_task_runner():
    def example_demo():
        key = "import_file_uploader"
        st.file_uploader(
            "Upload a CSV or excel file",
            type=Table.ALLOWED_FILE_FORMATS,
            key=key,
            on_change=lambda: _import_file_to_table(key),
        )

        imported_table: Table = st.session_state.get("imported_table")
        if imported_table is None:
            st.write("No table imported yet.")
        else:
            st.write("Imported table:")
            st.dataframe(imported_table.get_data())

    code = """import streamlit as st
import os
from gws_core import (File, FileHelper, Settings, Table, TableImporter, TaskOutputs)
from gws_streamlit_main import StreamlitTaskRunner

key = "import_file_uploader"
st.file_uploader("Upload a CSV or excel file",
                 type=Table.ALLOWED_FILE_FORMATS,
                 key=key, on_change=lambda: _import_file_to_table(key))

imported_table: Table = st.session_state.get("imported_table")
if imported_table is None:
    st.write("No table imported yet.")
else:
    st.write("Imported table:")
    st.dataframe(imported_table.get_data())

# method called when a file is uploaded
def _import_file_to_table(key: str) -> None:
    uploaded_file = st.session_state[key]
    if uploaded_file is not None:
        temp_dir = Settings.make_temp_dir()
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        # convert the file to table
        task_config = StreamlitTaskRunner(TableImporter)
        file = File(temp_file_path)
        task_config.generate_form_dialog(
            inputs={TableImporter.input_name: file},
            on_run_success=lambda result: _on_import_success(result, temp_dir)
        )

# method called once the dialog is closed and the task is successfully run
def _on_import_success(result: TaskOutputs, temp_dir: str):
    table = result[TableImporter.output_name]
    st.session_state["imported_table"] = table
    FileHelper.delete_dir(temp_dir)"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Task runner with file upload",
        description="Upload a file and run a task to process it. The task configuration is displayed in a dialog.",
        doc_func=StreamlitTaskRunner.generate_form_dialog,
    )


# method called when a file is uploaded
def _import_file_to_table(key: str) -> None:
    uploaded_file = st.session_state[key]
    if uploaded_file is not None:
        temp_dir = Settings.make_temp_dir()

        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # convert the file to table
        task_config = StreamlitTaskRunner(TableImporter)

        file = File(temp_file_path)
        task_config.generate_form_dialog(
            inputs={TableImporter.input_name: file},
            on_run_success=lambda result: _on_import_success(result, temp_dir),
        )


# method called once the dialog is closed and the task is successfully run


def _on_import_success(result: TaskOutputs, temp_dir: str):
    table = result[TableImporter.output_name]
    st.session_state["imported_table"] = table
    FileHelper.delete_dir(temp_dir)
