
import streamlit as st
from pandas import DataFrame

from gws_core.streamlit import StreamlitContainers, dataframe_paginated
from gws_core.test.data_provider import DataProvider


def render_dataframes_page():

    st.title('Dataframes')
    st.info('This page contains a showcase for custom streamlit component for dataframe.')

    dataframe = DataProvider.get_iris_table().get_data()
    _render_full_width_dataframe_container(dataframe)
    _render_dataframe_paginated(dataframe)


def _render_full_width_dataframe_container(df: DataFrame):
    st.subheader('Full width dataframe container')
    st.info('This allow the dataframe to take the full width of the container (with use_container_width=True option) without creating a horizontal scroll.')

    with StreamlitContainers.full_width_dataframe_container('container-full-dataframe'):
        st.dataframe(df, use_container_width=True)

    st.code('''
from gws_core.streamlit import StreamlitContainers

with StreamlitContainers.full_width_dataframe_container('container-full-dataframe'):
    st.dataframe(dataframe, use_container_width=True)
''')

    st.divider()


def _render_dataframe_paginated(df: DataFrame):
    st.subheader('Paginated dataframe')
    st.write("Row pagination")

    dataframe_paginated(df, paginate_rows=True, row_page_size_options=[25, 50, 100],
                        # apply a style to the dataframe
                        transformer=lambda df: df.style.format(thousands=" ", precision=1),
                        key='row_paginated')

    st.code('''

from gws_core.streamlit import dataframe_paginated

dataframe_paginated(df, paginate_rows=True, row_page_size_options=[25, 50, 100],
    # apply a style to the dataframe
    transformer=lambda df: df.style.format(thousands=" ", precision=1),
    key='row_paginated')
''')

    st.write("Column pagination")
    df_t = df.T
    dataframe_paginated(df_t, paginate_rows=False, paginate_columns=True, column_page_size_options=[25, 50, 100],
                        key='column_paginated')

    st.code('''
dataframe_paginated(df_t, paginate_rows=False, paginate_columns=True, column_page_size_options=[25, 50, 100],
    key='column_paginated')
''')

    st.divider()
