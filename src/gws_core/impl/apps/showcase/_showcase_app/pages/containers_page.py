
import streamlit as st

from gws_core.streamlit import StreamlitContainers


def render_containers_page():
    st.title('Resource Page')
    st.info('This page contains a showcase for custom streamlit containers.')

    _render_center_container()
    _render_row_container()
    _render_column_with_fit_content()
    _render_full_min_height_container()
    _render_container_with_style()


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
        """
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
        box-sizing: content-box;
    }
    """
    with StreamlitContainers.container_with_style('container-with-style', style):
        st.info('Render a component with style. Use [CLASS_NAME] to target the container.')

        st.code(f'''
        import streamlit as st
        from gws_core.streamlit import StreamlitContainer
        style = """{style}"""
        with StreamlitContainer.container_with_style('container-with-style', style):
            st.write('This is a container with style')
        ''')

    st.divider()
