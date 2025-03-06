
import os

import streamlit as st
from auto_ml_components import select_current_table_with_preview
from auto_ml_state import AutoMlState

from gws_core import (File, FileHelper, Settings, Table, TableImporter,
                      TaskOutputs)
from gws_core.streamlit import StreamlitTaskRunner


def _import_file_to_table(key: str) -> None:
    uploaded_file = st.session_state[key]
    if uploaded_file is not None:
        temp_dir = Settings.make_temp_dir()

        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        # convert the file to table
        task_config = StreamlitTaskRunner(TableImporter, key="table_importer")

        file = File(temp_file_path)
        task_config.generate_form_dialog(
            inputs={TableImporter.input_name: file},
            on_run_success=lambda result: _on_import_success(result, temp_dir)
        )


def _on_import_success(result: TaskOutputs, temp_dir: str):
    table = result[TableImporter.output_name]
    AutoMlState.add_table(table, table.name, set_current=True)
    FileHelper.delete_dir(temp_dir)


def render_import_page():

    st.subheader("Import data")

    st.info("Import a CSV or excel file to start working with your data. The file is not stored on the server and the data is cleaned when you close the app.")

    key = "import_file_uploader"
    st.file_uploader("Upload a CSV or excel file",
                     type=Table.ALLOWED_FILE_FORMATS,
                     key=key, on_change=lambda: _import_file_to_table(key))

    if AutoMlState.has_current_table():
        select_current_table_with_preview(dataframe_height=300)
