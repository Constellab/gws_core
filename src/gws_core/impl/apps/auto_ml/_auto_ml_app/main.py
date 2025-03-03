
import importlib.util

import auto_ml_transform_page
import streamlit as st
from auto_ml_main_page import render_table_page
from pandas import DataFrame, read_csv
from smart_plot_page import render_smart_plot_page
from smart_transformer_page import render_smart_transformer_page

sources: list


########################## TEST ##########################

csv_path = '/lab/user/bricks/gws_core/src/gws_core/impl/apps/auto_ml/_auto_ml_app/irisgood.csv'
# load from csv with header and ';' separator
df: DataFrame = read_csv(csv_path, sep=';')

# Generate a scatter plot with column 'one' as x and column 'two' as y. Use column 'five' as color.

# Remove column 'one' and 'two' from the table.
########################## TEST ##########################

if not "count" in st.session_state:
    st.session_state["count"] = 0

st.write(st.session_state["count"])

st.session_state["count"] += 1


def _render_table_page():
    render_table_page(df)


def _render_smart_plot_page():
    render_smart_plot_page(df)


def _render_smart_transformer_page():
    render_smart_transformer_page(df)


def _render_transformer_page():
    # TODO REMOVE
    importlib.reload(auto_ml_transform_page)
    auto_ml_transform_page.render_transformer_page(df)


def list_page():
    st.title("List of Elements")
    for i, row in df.iterrows():
        st.write(f"Element {i}: {row['one']}, {row['two']}, {row['three']}")
        if st.button(f"View Details {i}", key=f"button_{i}"):
            st.page_link(page=f"smart-plots")


def detail_page():
    element_id = st.query_params.id
    st.title(f"Detail Page for Element {element_id}")
    # element = df.iloc[element_id]
    # st.write(element)


tables_page = st.Page(list_page, title='Table', url_path='table', icon='📄')
plots_page = st.Page(detail_page, title='Plots', url_path='smart-plots', icon='📈')

pg = st.navigation([tables_page, plots_page])

pg.run()

# tables_page = st.Page(_render_table_page, title='Table', url_path='table', icon='📄')
# plots_page = st.Page(_render_smart_plot_page, title='Plots', url_path='smart-plots', icon='📈')
# ai_transformer_page = st.Page(_render_smart_transformer_page, title='AI Transformer',
#                               url_path='ai-transform', icon='✨')
# manual_transformer_page = st.Page(_render_transformer_page, title='Manual Transformer',
#                                   url_path='manual-transform', icon='📄')

# pg = st.navigation([tables_page, plots_page, ai_transformer_page, manual_transformer_page])

# pg.run()
