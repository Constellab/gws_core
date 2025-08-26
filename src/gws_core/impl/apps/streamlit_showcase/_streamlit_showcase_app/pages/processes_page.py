import os

import streamlit as st

from gws_core import (File, FileHelper, Settings, Table, TableImporter,
                      TaskOutputs)
from gws_core.streamlit import StreamlitTaskRunner


def render_processes_page():
    st.title("Processes")
    st.info("This page contains a showcase for streamlit component to interact with tasks and protocols.")

    _render_task_config_form()

    st.divider()

    _render_task_config_form_in_dialog()

    st.divider()

    _render_task_runner()


def _render_task_config_form():

    st.subheader("Task configuration form")

    if "config_data" not in st.session_state:
        st.session_state["config_data"] = None

    form_config = StreamlitTaskRunner(TableImporter)
    form_config.generate_config_form_without_run(
        session_state_key="config_data", default_config_values=TableImporter.config_specs.get_default_values())

    st.write(f"Task config : {st.session_state['config_data']}")

    st.code('''
        import streamlit as st
        from gws_core import TableImporter
        from gws_core.streamlit import StreamlitTaskRunner

        if "config_data" not in st.session_state:
            st.session_state["config_data"] = None

        form_config = StreamlitTaskRunner(TableImporter)
        form_config.generate_config_form_without_run(session_state_key="config_data", default_config_values=TableImporter.config_specs.get_default_values())

        st.write(f"Task config : {st.session_state['config_data']}")
    ''')


def _render_task_config_form_in_dialog():
    st.subheader("Task configuration form in dialog")

    if "config_data_dialog" not in st.session_state:
        st.session_state["config_data_dialog"] = None

    @st.dialog("Task Configuration")
    def dialog():
        form_config = StreamlitTaskRunner(TableImporter)
        form_config.generate_config_form_without_run(
            session_state_key="config_data_dialog", default_config_values=TableImporter.config_specs.get_default_values(),
            key="config-task-form-dialog")

        if st.button("Save"):
            st.rerun()

        st.write(f"Task config : {st.session_state['config_data_dialog']}")

    if st.button("Open Config form dialog"):
        dialog()

    st.write(f"Task config : {st.session_state['config_data_dialog']}")

    st.code('''
        import streamlit as st
        from gws_core import TableImporter
        from gws_core.streamlit import StreamlitTaskRunner

        if "config_data_dialog" not in st.session_state:
        st.session_state["config_data_dialog"] = None

        @st.dialog("Task Configuration")
        def dialog():
            form_config = StreamlitTaskRunner(TableImporter)
            form_config.generate_config_form_without_run(
                session_state_key="config_data_dialog", default_config_values=TableImporter.config_specs.get_default_values(),
                key="config-task-form-dialog")

            if st.button("Save"):
                st.rerun()

            st.write(f"Task config : {st.session_state['config_data_dialog']}")

        if st.button("Open Config form dialog"):
            dialog()

        st.write(f"Task config : {st.session_state['config_data_dialog']}")

    ''')


def _render_task_runner():
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
