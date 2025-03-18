
import streamlit as st

from gws_core.streamlit import StreamlitContainers, StreamlitGridCell


def render_containers_page():
    st.title('Containers')
    st.info('This page contains a showcase for custom streamlit containers.')

    st.divider()

    _render_center_container()
    _render_row_container()
    _render_column_with_fit_content()
    _render_full_min_height_container()
    _render_container_with_style()
    _render_grid()
    _render_exception_container()


def _render_center_container():
    st.subheader('Centered container')
    style = """
[CLASS_NAME] {
    border: 3px dashed lightblue;
    padding: 1em;
}
"""
    with StreamlitContainers.container_centered('container-center', max_width='48em', additional_style=style):
        st.write('This is a centered container')

        st.code(f'''
import streamlit as st
from gws_core.streamlit import StreamlitContainer

style = """{style}"""

with StreamlitContainer.container_centered('container-center', max_width='48em',
            additional_style=style):
    st.write('This is a centered container')
''')

    st.divider()


def _render_row_container():
    st.subheader('Row container')
    style = """
[CLASS_NAME] {
    border: 3px dashed lightblue;
    padding: 1em;
}
"""
    with StreamlitContainers.row_container('container-row', flow='row wrap',
                                           vertical_align_items='center',
                                           additional_style=style):
        st.write('This is a row container')
        st.button('Button 1')
        st.button('Button 2')
        st.button('Button 3')

    st.code(f'''
import streamlit as st
from gws_core.streamlit import StreamlitContainer

style = """{style}"""
with StreamlitContainers.row_container('container-row', flow='row wrap',
                                        vertical_align_items='center',
                                        additional_style=style):
    st.write('This is a row container')
    st.button('Button 1')
    st.button('Button 2')
    st.button('Button 3')
''')

    st.divider()


def _render_column_with_fit_content():
    st.subheader('Column with fit content')
    style = """
[CLASS_NAME] {
    border: 3px dashed lightblue;
    padding: 1em;
}
"""
    title_col, button_col = StreamlitContainers.columns_with_fit_content(
        'container-column', cols=[1, 'fit-content'], additional_style=style)
    with title_col:
        st.write('This column takes max space')

    with button_col:
        st.button('Column size is fit to content')

    st.code(f'''
import streamlit as st
from gws_core.streamlit import StreamlitContainer

style = """{style}"""
title_col, button_col = StreamlitContainer.columns_with_fit_content('container-column', cols=[1, 'fit-content'])
with title_col:
    st.write('This column takes max space')
with button_col:
    st.button('Column size is fit to content')
''')

    st.divider()


def _render_full_min_height_container():
    st.subheader('Full min height container')

    style = """
[CLASS_NAME] {
    border: 3px dashed lightblue;
    box-sizing: content-box;
}
"""

    with StreamlitContainers.container_full_min_height('container-full-min-height', additional_style=style):
        st.info('This allow the container to take at minimum the full height of the page.')

    st.code(f'''
import streamlit as st
from gws_core.streamlit import StreamlitContainer

style = """{style}"""
with StreamlitContainer.container_full_min_height('container-full-min-height', additional_style=style):
    st.info('This allow the container to take at minimum the full height of the page.')
''')

    st.divider()


def _render_container_with_style():
    st.subheader('Container with style')
    style = """
[CLASS_NAME] {
    border: 3px dashed lightblue;
}
"""
    with StreamlitContainers.container_with_style('container-with-style', style):
        st.info('Render a component with style (using css). Use [CLASS_NAME] to target the container.')

    st.code(f'''
import streamlit as st
from gws_core.streamlit import StreamlitContainer

style = """{style}"""
with StreamlitContainer.container_with_style('container-with-style', style):
    st.write('This is a container with style')
''')

    st.divider()


def _render_grid():

    st.subheader('Grid container')

    st.info('Use the grid container to create a grid layout. The grid cells are defined by StreamlitGridCell objects.')

    grid_cells = [
        StreamlitGridCell(col_span=3, row_span=1, style="""
    [CLASS_NAME] {
        border: solid black;
    }
    """),
        StreamlitGridCell(col_span=1, row_span=2, style="""
    [CLASS_NAME] {
        border: dotted blue;
    }
    """),
        StreamlitGridCell(col_span=1, row_span=2, style="""
    [CLASS_NAME] {
        border: dashed red;
    }
    """),
        StreamlitGridCell(col_span=1, row_span=1, style="""
    [CLASS_NAME] {
        border: thick solid yellow;
    }
    """),
        StreamlitGridCell(col_span=1, row_span=2, style="""
    [CLASS_NAME] {
        border: 3px solid purple;
    }
    """),
        StreamlitGridCell(col_span=2, row_span=1, style="""
    [CLASS_NAME] {
        border: medium dashed cyan;
    }
    """),
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
        st.write('sixth cell')

    st.code('''
import streamlit as st
from gws_core.streamlit import StreamlitContainer

grid_cells = [
    StreamlitGridCell(col_span=3, row_span=1, style="""
[CLASS_NAME] {
    border: solid black;
}
"""),
    StreamlitGridCell(col_span=1, row_span=2, style="""
[CLASS_NAME] {
    border: dotted blue;
}
"""),
    StreamlitGridCell(col_span=1, row_span=2, style="""
[CLASS_NAME] {
    border: dashed red;
}
"""),
    StreamlitGridCell(col_span=1, row_span=1, style="""
[CLASS_NAME] {
    border: thick solid yellow;
}
"""),
    StreamlitGridCell(col_span=1, row_span=, style="""
[CLASS_NAME] {
    border: 3px solid purple;
}
"""),
    StreamlitGridCell(col_span=2, row_span=1, style="""
[CLASS_NAME] {
    border: medium dashed cyan;
}
"""),
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
    st.write('sixth cell')

''')
    st.divider()


@StreamlitContainers.fragment(key='exception-container-fragment')
def _render_exception_container():
    st.subheader('Exception container')

    st.info('Use the exception container to display an exception message in a container.' +
            'In constellab app the error is catch and this container is used by default')
    style = """
    [CLASS_NAME] {
    border: 3px dashed lightblue;
    padding: 1em;
}
"""
    with StreamlitContainers.container_with_style('exception', style):
        try:
            raise Exception('An exception occurred')
        except Exception as e:
            StreamlitContainers.exception_container(key='exception-container',
                                                    error_text='Custom message',
                                                    exception=e)

    st.code('''
import streamlit as st
from gws_core.streamlit import StreamlitContainer

try:
    raise Exception('An exception occurred')
except Exception as e:
    StreamlitContainer.exception_container(key='exception-container',
                                           error_text='Custom message',
                                           exception=e)
''')

    st.warning('When using the default `st.fragment()`, the exception is not catch automatically and the app will crash.' +
               'Use the `StreamlitContainers.fragment()` to catch the exception and display it in a container.')

    st.code('''
from gws_core.streamlit import StreamlitContainers

@StreamlitContainers.fragment(key='exception-container-fragment')
def method_that_can_raise_exception():
    raise Exception('An exception occurred')
''')
    st.divider()
