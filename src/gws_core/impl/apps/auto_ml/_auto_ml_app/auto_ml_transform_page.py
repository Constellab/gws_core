
import streamlit as st
from pandas import DataFrame

from gws_core import TableRowConcat, TableRowSelector
from gws_core.streamlit import StreamlitTaskConfig, rich_text_editor


@st.fragment
def render_transformer_page(data: DataFrame):

    st.header("Transformer Page")

    task_config = StreamlitTaskConfig(TableRowConcat, key='process-config')
    if st.button("Concatenate the rows"):
        task_config.generate_form_dialog()

    st.write(task_config.get_dialog_value())

    # rich_text_editor()
