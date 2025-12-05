import streamlit as st
from gws_core.streamlit import StreamlitContainers, StreamlitGridCell

from ..components.example_tabs_component import example_tabs
from ..components.page_layout_component import page_layout


def render_containers_page():
    def page_content():
        _render_center_container()
        _render_row_container()
        _render_column_with_fit_content()
        _render_full_min_height_container()
        _render_container_with_style()
        _render_grid()
        _render_exception_container()

    page_layout(
        title="Containers",
        description="This page contains a showcase for custom streamlit containers.",
        content_function=page_content,
    )


def _render_center_container():
    def example_demo():
        style = """
[CLASS_NAME] {
    border: 3px dashed lightblue;
    padding: 1em;
}
"""
        with StreamlitContainers.container_centered(
            "container-center", max_width="48em", additional_style=style
        ):
            st.write("This is a centered container")

    code = """import streamlit as st
from gws_core.streamlit import StreamlitContainers

style = \"\"\"
[CLASS_NAME] {
    border: 3px dashed lightblue;
    padding: 1em;
}
\"\"\"

with StreamlitContainers.container_centered('container-center', max_width='48em',
            additional_style=style):
    st.write('This is a centered container')"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Centered container",
        description="A container that centers its content with a maximum width.",
        doc_func=StreamlitContainers.container_centered,
    )


def _render_row_container():
    def example_demo():
        style = """
[CLASS_NAME] {
    border: 3px dashed lightblue;
    padding: 1em;
}
"""
        with StreamlitContainers.row_container(
            "container-row",
            flow="row wrap",
            vertical_align_items="center",
            gap="50px",
            additional_style=style,
        ):
            st.write("This is a row container")
            st.button("Button 1")
            st.button("Button 2")
            st.button("Button 3")

    code = """import streamlit as st
from gws_core.streamlit import StreamlitContainers

style = \"\"\"
[CLASS_NAME] {
    border: 3px dashed lightblue;
    padding: 1em;
}
\"\"\"
with StreamlitContainers.row_container('container-row', flow='row wrap',
                                        vertical_align_items='center',
                                        gap='50px',
                                        additional_style=style):
    st.write('This is a row container')
    st.button('Button 1')
    st.button('Button 2')
    st.button('Button 3')"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Row container",
        description="A container that arranges elements in a row with flex layout.",
        doc_func=StreamlitContainers.row_container,
    )


def _render_column_with_fit_content():
    def example_demo():
        style = """
[CLASS_NAME] {
    border: 3px dashed lightblue;
    padding: 1em;
}
"""
        title_col, button_col = StreamlitContainers.columns_with_fit_content(
            "container-column",
            cols=[1, "fit-content"],
            vertical_align_items="center",
            additional_style=style,
        )
        with title_col:
            st.write("This column takes max space")

        with button_col:
            st.button("Column size is fit to content")

    code = """import streamlit as st
from gws_core.streamlit import StreamlitContainers

style = \"\"\"
[CLASS_NAME] {
    border: 3px dashed lightblue;
    padding: 1em;
}
\"\"\"
title_col, button_col = StreamlitContainers.columns_with_fit_content('container-column', cols=[1, 'fit-content'],
        vertical_align_items='center',
        additional_style=style)
with title_col:
    st.write('This column takes max space')
with button_col:
    st.button('Column size is fit to content')"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Column with fit content",
        description="Columns that support both flexible and fit-content widths.",
        doc_func=StreamlitContainers.columns_with_fit_content,
    )


def _render_full_min_height_container():
    def example_demo():
        style = """
[CLASS_NAME] {
    border: 3px dashed lightblue;
    box-sizing: content-box;
}
"""
        with StreamlitContainers.container_full_min_height(
            "container-full-min-height", additional_style=style
        ):
            st.info("This allows the container to take at minimum the full height of the page.")

    code = """import streamlit as st
from gws_core.streamlit import StreamlitContainers

style = \"\"\"
[CLASS_NAME] {
    border: 3px dashed lightblue;
    box-sizing: content-box;
}
\"\"\"
with StreamlitContainers.container_full_min_height('container-full-min-height', additional_style=style):
    st.info('This allows the container to take at minimum the full height of the page.')"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Full min height container",
        description="A container that takes at least the full height of the page.",
        doc_func=StreamlitContainers.container_full_min_height,
    )


def _render_container_with_style():
    def example_demo():
        style = """
[CLASS_NAME] {
    border: 3px dashed lightblue;
}
"""
        with StreamlitContainers.container_with_style("container-with-style", style):
            st.info(
                "Render a component with style (using css). Use [CLASS_NAME] to target the container."
            )

    code = """import streamlit as st
from gws_core.streamlit import StreamlitContainers

style = \"\"\"
[CLASS_NAME] {
    border: 3px dashed lightblue;
}
\"\"\"
with StreamlitContainers.container_with_style('container-with-style', style):
    st.write('This is a container with style')"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Container with style",
        description="A container with custom CSS styling.",
        doc_func=StreamlitContainers.container_with_style,
    )


def _render_grid():
    def example_demo():
        grid_cells = [
            StreamlitGridCell(
                col_span=3,
                row_span=1,
                style="""
    [CLASS_NAME] {
        border: solid black;
    }
    """,
            ),
            StreamlitGridCell(
                col_span=1,
                row_span=2,
                style="""
    [CLASS_NAME] {
        border: dotted blue;
    }
    """,
            ),
            StreamlitGridCell(
                col_span=1,
                row_span=2,
                style="""
    [CLASS_NAME] {
        border: dashed red;
    }
    """,
            ),
            StreamlitGridCell(
                col_span=1,
                row_span=1,
                style="""
    [CLASS_NAME] {
        border: thick solid yellow;
    }
    """,
            ),
            StreamlitGridCell(
                col_span=1,
                row_span=2,
                style="""
    [CLASS_NAME] {
        border: 3px solid purple;
    }
    """,
            ),
            StreamlitGridCell(
                col_span=2,
                row_span=1,
                style="""
    [CLASS_NAME] {
        border: medium dashed cyan;
    }
    """,
            ),
        ]
        cell1, cell2, cell3, cell4, cell5, cell6 = StreamlitContainers.grid_container(
            nb_columns=3, cells=grid_cells, key="custom-grid", row_height="100px", gap="10px"
        )

        with cell1:
            st.write("First cell. Col span 3. Row span 1")
        with cell2:
            st.write("Second cell. Col span 1. Row span 2")
        with cell3:
            st.write("Third cell. Col span 1. Row span 2")
        with cell4:
            st.write("Fourth cell. Col span 1. Row span 1")
        with cell5:
            st.write("Fifth cell. Col span 1. Row span 2")
        with cell6:
            st.write("Sixth cell. Col span 2. Row span 1")

    code = """import streamlit as st
from gws_core.streamlit import StreamlitContainers, StreamlitGridCell

grid_cells = [
    StreamlitGridCell(col_span=3, row_span=1, style=\"\"\"
[CLASS_NAME] {
    border: solid black;
}
\"\"\"),
    StreamlitGridCell(col_span=1, row_span=2, style=\"\"\"
[CLASS_NAME] {
    border: dotted blue;
}
\"\"\"),
    StreamlitGridCell(col_span=1, row_span=2, style=\"\"\"
[CLASS_NAME] {
    border: dashed red;
}
\"\"\"),
    StreamlitGridCell(col_span=1, row_span=1, style=\"\"\"
[CLASS_NAME] {
    border: thick solid yellow;
}
\"\"\"),
    StreamlitGridCell(col_span=1, row_span=2, style=\"\"\"
[CLASS_NAME] {
    border: 3px solid purple;
}
\"\"\"),
    StreamlitGridCell(col_span=2, row_span=1, style=\"\"\"
[CLASS_NAME] {
    border: medium dashed cyan;
}
\"\"\"),
]
cell1, cell2, cell3, cell4, cell5, cell6 = StreamlitContainers.grid_container(
    nb_columns=3, cells=grid_cells, key='grid', row_height='100px', gap='10px')

with cell1:
    st.write('first cell')
with cell2:
    st.write('second cell')
with cell3:
    st.write('third cell')
with cell4:
    st.write('fourth cell')
with cell5:
    st.write('fifth cell')
with cell6:
    st.write('sixth cell')"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Grid container",
        description="Use the grid container to create a grid layout. The grid cells are defined by StreamlitGridCell objects.",
        doc_func=StreamlitContainers.grid_container,
    )


@StreamlitContainers.fragment(key="exception-container-fragment")
def _render_exception_container():
    def example_demo():
        style = """
    [CLASS_NAME] {
    border: 3px dashed lightblue;
    padding: 1em;
}
"""
        with StreamlitContainers.container_with_style("exception", style):
            try:
                raise Exception("An exception occurred")
            except Exception as e:
                StreamlitContainers.exception_container(
                    key="exception-container", error_text="Custom message", exception=e
                )

        st.warning(
            "When using the default `st.fragment()`, the exception is not caught automatically and the app will crash. "
            + "Use `StreamlitContainers.fragment()` to catch the exception and display it in a container."
        )

        st.code("""from gws_core.streamlit import StreamlitContainers

@StreamlitContainers.fragment(key='exception-container-fragment')
def method_that_can_raise_exception():
    raise Exception('An exception occurred')
""")

    code = """import streamlit as st
from gws_core.streamlit import StreamlitContainers

try:
    raise Exception('An exception occurred')
except Exception as e:
    StreamlitContainers.exception_container(key='exception-container',
                                           error_text='Custom message',
                                           exception=e)"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Exception container",
        description="Use the exception container to display an exception message. In constellab app the error is caught and this container is used by default.",
        doc_func=StreamlitContainers.exception_container,
    )
