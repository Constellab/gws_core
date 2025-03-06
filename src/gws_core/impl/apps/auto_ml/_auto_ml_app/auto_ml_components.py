

import streamlit as st
from auto_ml_state import AutoMlState, TableInfo

from gws_core.streamlit import StreamlitContainer


def select_current_table_with_preview(dataframe_height: int = 300) -> TableInfo:
    result = select_current_table()

    with StreamlitContainer.full_dataframe_container('current-table'):
        st.dataframe(result.get_dataframe(), use_container_width=True,
                     height=dataframe_height, key="select_table_dataframe")

    return result


def _on_table_selected(key: str):
    selected = st.session_state[key]
    AutoMlState.set_current_table(selected.id)


def select_current_table() -> TableInfo:
    tables = st.session_state.get("tables", [])
    current_table = st.session_state.get("current_table")
    current_index = tables.index(current_table)

    # To correctly work on multiple pages, we need to use the same ke yfor each page and a key
    # different than the real state and update the real state when the select box is changed
    key = "select_table_select_current_table"
    selected: TableInfo = st.selectbox("Current table", tables, format_func=str,
                                       index=current_index,
                                       on_change=lambda: _on_table_selected(key),
                                       key=key)

    return selected
