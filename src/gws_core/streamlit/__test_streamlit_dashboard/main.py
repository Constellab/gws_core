
import streamlit as st

from gws_core.impl.table.table import Table
from gws_core.streamlit import ResourceSearchInput

st.title("Hello World")

ResourceSearchInput().add_resource_type_filter(Table).add_flagged_filter(True).select()
