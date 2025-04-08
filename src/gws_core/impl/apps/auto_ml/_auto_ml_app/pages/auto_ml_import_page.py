
import streamlit as st
from auto_ml_components import select_current_table_with_preview
from auto_ml_state import AutoMlState

from gws_core import File, FileHelper, Table, TableImporter, TaskOutputs
from gws_core.streamlit import StreamlitHelper, StreamlitTaskRunner
from gws_core.test.data_provider import DataProvider


def _import_file_to_table(key: str) -> None:
    uploaded_file = st.session_state[key]
    if uploaded_file is not None:

        temp_file_path = StreamlitHelper.store_uploaded_file_in_tmp_dir(uploaded_file)

        # convert the file to table
        task_config = StreamlitTaskRunner(TableImporter)

        file = File(temp_file_path)
        task_config.generate_form_dialog(
            inputs={TableImporter.input_name: file},
            on_run_success=lambda result: _on_import_success(result, temp_file_path)
        )


def _on_import_success(result: TaskOutputs, temp_file_path: str):
    table = result[TableImporter.output_name]
    AutoMlState.add_table(table, table.name, set_current=True)
    FileHelper.delete_file(temp_file_path)


def render_import_page():

    st.subheader("Import data")

    st.info("Import a CSV or excel file to start working with your data. The file is not stored on the server and the data is cleaned when you close the app.")

    key = "import_file_uploader"
    st.file_uploader("Upload a CSV or excel file",
                     type=Table.ALLOWED_FILE_FORMATS,
                     key=key, on_change=lambda: _import_file_to_table(key))

    if st.button('Load iris dataset'):
        AutoMlState.add_table(DataProvider.get_iris_table(), 'iris', set_current=True)
        st.rerun()

    if AutoMlState.has_current_table():
        select_current_table_with_preview(dataframe_height=300)
