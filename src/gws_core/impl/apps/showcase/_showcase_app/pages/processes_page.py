import os

import streamlit as st
from showcase_core import ShowcaseCore

from gws_core import File, FileHelper, Settings, TableImporter, TaskOutputs
from gws_core.streamlit import StreamlitTaskRunner


def render_processes_page():
    st.title("Processes")
    st.info("This page contains a showcase for streamlit component to interact with tasks and protocols. The preview is not enable yet")

    ShowcaseCore.show_requires_authentication_warning()

    _render_task_runner()


def _render_task_runner():
    # key = "import_file_uploader"
    # st.file_uploader("Upload a CSV or excel file",
    #                  type=Table.ALLOWED_FILE_FORMATS,
    #                  key=key, on_change=lambda: _import_file_to_table(key))

    # imported_table: Table = st.session_state.get("imported_table")
    # if imported_table is None:
    #     st.write("No table imported yet.")
    # else:
    #     st.write("Imported table:")
    #     st.dataframe(imported_table.get_data())

    _render_code()


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
    FileHelper.delete_dir(temp_dir)


def _render_code():
    st.divider()
    st.subheader("Code")
    st.code('''
import streamlit as st
from gws_core import (File, FileHelper, Settings, Table, TableImporter,
                    TaskOutputs)
from gws_core.streamlit import StreamlitTaskRunner

def render():
    key = "import_file_uploader"
    st.file_uploader("Upload a CSV or excel file",
                    type=Table.ALLOWED_FILE_FORMATS,
                    key=key, on_change=lambda: _import_file_to_table(key))

    imported_table: Table = st.session_state.get("imported_table")
    if imported_table is None:
        st.write("No table imported yet.")
    else:
        st.write("Imported table:")
        st.dataframe(imported_table.get_data())'

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
    FileHelper.delete_dir(temp_dir)
''')
