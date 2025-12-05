import streamlit as st
from gws_core.streamlit import StreamlitContainers, dataframe_paginated
from pandas import DataFrame

from ..components.example_tabs_component import example_tabs
from ..components.page_layout_component import page_layout


def render_dataframes_page():
    dataframe = DataFrame(
        {
            "A": range(1, 101),
            "B": [x * 2 for x in range(1, 101)],
            "C": [x**2 for x in range(1, 101)],
            "D": [x**0.5 for x in range(1, 101)],
            "E": ["Category 1" if x % 2 == 0 else "Category 2" for x in range(1, 101)],
            "F": ["Text " + str(x) for x in range(1, 101)],
        }
    )

    def page_content():
        _render_full_width_dataframe_container(dataframe)
        _render_dataframe_paginated(dataframe)

    page_layout(
        title="Dataframes",
        description="This page contains a showcase for custom streamlit component for dataframe.",
        content_function=page_content,
    )


def _render_full_width_dataframe_container(df: DataFrame):
    def example_demo():
        with StreamlitContainers.full_width_dataframe_container("container-full-dataframe"):
            st.dataframe(df, width="stretch")

    code = """import streamlit as st
from gws_core.streamlit import StreamlitContainers

with StreamlitContainers.full_width_dataframe_container('container-full-dataframe'):
    st.dataframe(dataframe, width='stretch')"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Full width dataframe container",
        description="This allows the dataframe to take the full width of the container (with width='stretch' option) without creating a horizontal scroll.",
        doc_func=StreamlitContainers.full_width_dataframe_container,
    )


def _render_dataframe_paginated(df: DataFrame):
    def example_demo():
        st.write("Row pagination")
        dataframe_paginated(
            df,
            paginate_rows=True,
            row_page_size_options=[25, 50, 100],
            # apply a style to the dataframe
            transformer=lambda df: df.style.format(thousands=" ", precision=1),
            key="row_paginated",
        )

        st.write("Column pagination")
        df_t = df.T
        dataframe_paginated(
            df_t,
            paginate_rows=False,
            paginate_columns=True,
            column_page_size_options=[25, 50, 100],
            key="column_paginated",
        )

    code = """import streamlit as st
from gws_core.streamlit import dataframe_paginated

# Row pagination
dataframe_paginated(df, paginate_rows=True, row_page_size_options=[25, 50, 100],
    # apply a style to the dataframe
    transformer=lambda df: df.style.format(thousands=" ", precision=1),
    key='row_paginated')

# Column pagination
df_t = df.T
dataframe_paginated(df_t, paginate_rows=False, paginate_columns=True, column_page_size_options=[25, 50, 100],
    key='column_paginated')"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Paginated dataframe",
        description="Dataframe with row and column pagination support.",
        doc_func=dataframe_paginated,
    )
