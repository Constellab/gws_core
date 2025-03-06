

import streamlit as st
from auto_ml_state import AutoMlState
from pages import (auto_ml_ai_plot_page, auto_ml_ai_transform_page,
                   auto_ml_getting_started_page, auto_ml_import_page,
                   auto_ml_manual_transform_page, auto_ml_tables_page)

from gws_core.impl.apps.auto_ml._auto_ml_app.pages import \
    auto_ml_ai_multi_tables_page

sources: list


########################## TEST ##########################

# csv_path = '/lab/user/bricks/gws_core/tests/testdata/iris.csv'
# # load from csv with header and ';' separator
# df: DataFrame = read_csv(csv_path, sep=';')
# df_2: DataFrame = read_csv(csv_path, sep=';')
# df_2.drop(columns=['one', 'two'], inplace=True)
# # Generate a scatter plot with column 'one' as x and column 'two' as y. Use column 'five' as color.
# table = AutoMlState.get_current_table()
# if table is None:
#     AutoMlState.init(Table(df), 'iris')
#     AutoMlState.add_table(Table(df_2), 'another_iris')

# Remove column 'one' and 'two' from the table.
########################## TEST ##########################


# count = st.session_state.get('count', 0)
# st.write('Count:', count)
# st.session_state['count'] = count + 1

def _render_getting_started_page():
    # importlib.reload(auto_ml_getting_started_page)
    auto_ml_getting_started_page.render_getting_started_page(sources[0])


def _render_import_page():
    # importlib.reload(auto_ml_import_page)
    auto_ml_import_page.render_import_page()


def _render_tables_page():
    # importlib.reload(auto_ml_tables_page)
    auto_ml_tables_page.render_tables_page()


def _render_ai_plot_page():
    # importlib.reload(auto_ml_ai_plot_page)
    auto_ml_ai_plot_page.render_ai_plot_page()


def _render_ai_transform_page():
    # importlib.reload(auto_ml_ai_transform_page)
    auto_ml_ai_transform_page.render_ai_transform_page()


def _render_ai_multi_table_page():
    # importlib.reload(auto_ml_ai_multi_tables_page)
    auto_ml_ai_multi_tables_page.render_ai_multi_tables_page()


def _render_manual_transform_page():
    # importlib.reload(auto_ml_manual_transform_page)
    auto_ml_manual_transform_page.render_manual_transform_page()


getting_started_page = st.Page(_render_getting_started_page, title='Getting Started',
                               url_path='getting-started', icon='🚀')
import_page = st.Page(_render_import_page, title='Import', url_path='import', icon='⬆️')
tables_page = st.Page(_render_tables_page, title='Table', url_path='table', icon='📄')
plots_page = st.Page(_render_ai_plot_page, title='AI Plots', url_path='ai-plots', icon='✨')
ai_transformer_page = st.Page(_render_ai_transform_page, title='AI Transformer',
                              url_path='ai-transform', icon='✨')
multi_table_ai_page = st.Page(_render_ai_multi_table_page, title='Multi Tables AI', url_path='ai-multi-tables', icon='✨'
                              )
manual_transformer_page = st.Page(_render_manual_transform_page, title='Manual Transformer',
                                  url_path='manual-transform', icon='📄')

if AutoMlState.has_current_table():
    pg = st.navigation([getting_started_page, import_page,
                        tables_page, plots_page, ai_transformer_page,
                        multi_table_ai_page, manual_transformer_page])
else:
    pg = st.navigation([getting_started_page, import_page])

pg.run()
