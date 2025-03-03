

import streamlit as st
from pandas import DataFrame


def render_table_page(data: DataFrame) -> None:
    """Render the table page

    :param data: The data to render
    :type data: DataFrame
    """
    st.header("Table Page")
    st.dataframe(data)

    st.write(data.describe())
