

import streamlit as st
from auto_ml_components import select_current_table_with_preview


def render_tables_page() -> None:
    """Render the table page

    :param data: The data to render
    :type data: DataFrame
    """

    st.subheader("Tables")

    select_current_table_with_preview(dataframe_height=600)
