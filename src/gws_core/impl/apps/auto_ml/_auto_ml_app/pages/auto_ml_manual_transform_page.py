
from typing import Type

import streamlit as st
from auto_ml_components import select_current_table
from auto_ml_state import AutoMlState

from gws_core import (TableColumnAggregator, TableColumnsDeleter,
                      TableColumnSelector, TableReplace, TableRowAggregator,
                      TableRowsDeleter, TableRowSelector, TableScaler,
                      TableTransposer, Transformer)
from gws_core.streamlit import (StreamlitContainers, StreamlitHelper,
                                StreamlitTaskRunner)


def _call_transformer(transformer: Type[Transformer], suffix: str) -> None:
    current_table = AutoMlState.get_current_table()

    def on_success(result):
        name = current_table.original_name + " " + suffix
        AutoMlState.add_table(result[Transformer.output_name], name, set_current=True,
                              original_name=current_table.original_name)

    task_config = StreamlitTaskRunner(transformer, key='process-config')
    task_config.generate_form_dialog(
        inputs={Transformer.input_name: current_table.table},
        on_run_success=on_success)


@st.fragment
def render_manual_transform_page():

    col1, col2 = st.columns([1, 1])
    with col1:

        st.subheader("Manual transformers")

        st.info("In this page you can apply manual transformations to your table.")

        select_current_table()

        st.write('Generic')
        generic_col1, generic_col2, generic_col3 = st.columns(3)
        with generic_col1:
            if st.button("Transpose", use_container_width=True):
                _call_transformer(TableTransposer, "transposed")

        with generic_col2:
            if st.button("Scale", use_container_width=True):
                _call_transformer(TableScaler, "scaled")

        with generic_col3:
            if st.button("Replace", use_container_width=True):
                _call_transformer(TableReplace, "replaced")

        st.write('Columns')
        col_col1, col_col2, col_col3 = st.columns(3)
        with col_col1:
            if st.button("Filter columns", use_container_width=True):
                _call_transformer(TableColumnSelector, "column filtered")
        with col_col2:
            if st.button("Delete columns", use_container_width=True):
                _call_transformer(TableColumnsDeleter, "column deleted")
        with col_col3:
            if st.button("Aggregate columns", use_container_width=True):
                _call_transformer(TableColumnAggregator, "column aggregated")

        st.write('Rows')
        col_row1, col_row2, col_row3 = st.columns([1, 1, 1])
        with col_row1:
            if st.button("Filter rows", use_container_width=True):
                _call_transformer(TableRowSelector, "row filtered")
        with col_row2:
            if st.button("Delete rows", use_container_width=True):
                _call_transformer(TableRowsDeleter, "row deleted")
        with col_row3:
            if st.button("Aggregate rows", use_container_width=True):
                _call_transformer(TableRowAggregator, "row aggregated")

    with col2:
        style = f"""
        [CLASS_NAME]{{
            /* Padding to let space for the button above dataframe */
            padding-top: 30px;
        }}
        [CLASS_NAME] [data-testid="stDataFrameResizable"] {{
            min-height: {StreamlitHelper.get_page_height(30)} !important;
        }}
"""

        with StreamlitContainers.full_width_dataframe_container('right-container', style):
            st.dataframe(AutoMlState.get_current_table().table.get_data(),
                         use_container_width=True, key='current-table-dataframe')
