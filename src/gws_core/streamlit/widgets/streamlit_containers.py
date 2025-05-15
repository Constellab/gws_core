from typing import List, Literal

import streamlit as st

from .streamlit_helper import StreamlitHelper

FlexAlignItems = Literal['start', 'center', 'end', 'baseline', 'stretch']


class StreamlitGridCell():

    col_span: int
    row_span: int
    style: str

    def __init__(self, col_span: int, row_span: int, style: str = None):
        """Define a cell of a grid (for StreamlitContainers.container_grid method)

        :param col_span: number of columns spanned by the cell.
                        It will be passed to css like : grid-column: span {col_span}
        :type col_span: int
        :param row_span: number of rows spanned by the cell
                        It will be passed to css like : grid-row: span {row_span}
        :type row_span: int
        :param style: css style of the cell, defaults to None
        :type style: str, optional
        """
        self.col_span = col_span
        self.row_span = row_span
        self.style = style


class StreamlitContainers():

    @classmethod
    def container_centered(cls, key: str, max_width: str = '48em', additional_style: str = None):
        """Define a centered container with max width. Useful to center content like an article.

        :param key: key
        :type key: str
        :param max_width: max width of the container, defaults to '48em'
        :type max_width: str, optional
        :return: _description_
        :rtype: _type_
        """
        style = f"""
        [CLASS_NAME] {{
            max-width: {max_width};
            margin-inline: auto;
        }}
        """

        if additional_style:
            style += additional_style

        container = cls.container_with_style(key, style)
        return container.columns(1)[0]

    @classmethod
    def row_container(cls, key: str, flow: Literal['row', 'row wrap'] = 'row wrap',
                      vertical_align_items: FlexAlignItems = 'start',
                      gap: str = None,
                      additional_style: str = None):
        """Define a row container, element inside a in a row (like buttons, text...)

        :param key: key
        :type key: str
        :param flow: flex-flow style, defaults to 'row wrap'
        :type flow: Literal[&#39;row&#39;, &#39;row wrap&#39;], optional
        :param vertical_align_items: vertical align-items style, defaults to 'start'
        :type vertical_align_items: FlexAlignItems, optional
        :param gap: gap between elements, defaults to None
        :type gap: str, optional
        :param additional_style: additional css style, defaults to None
        :type additional_style: str, optional
        :return: _description_
        :rtype: _type_
        """
        style = f"""
            [CLASS_NAME] {{
                flex-flow: {flow};
                align-items: {vertical_align_items};
                gap: {gap};
            }}

            [CLASS_NAME] * {{
                width: fit-content !important;
            }}
            """

        if additional_style:
            style += additional_style
        return cls.container_with_style(key, style)

    @classmethod
    def columns_with_fit_content(cls, key: str, cols: List[int | Literal['fit-content']],
                                 vertical_align_items: FlexAlignItems = 'start',
                                 additional_style: str = None):
        """Define columns that also support fit content width.

        :param key: key
        :type key: str
        :param cols: list of columns width. Use 'fit-content' to define a column with fit content width
        :type cols: List[int | Literal['fit-content']]
        :param vertical_align_items: vertical align-items style, defaults to 'start'
        :type vertical_align_items: FlexAlignItems, optional
        :param additional_style: additional css style, defaults to None
        :type additional_style: str, optional
        :return: _description_
        :rtype: _type_
        """

        style: str = ''

        int_cols = []
        for i, col in enumerate(cols):
            if col == 'fit-content':
                style += f"""
        [CLASS_NAME] .stColumn:nth-of-type({i + 1}) {{
            width: fit-content !important;
            flex: initial !important;
        }}
        [CLASS_NAME] .stColumn:nth-of-type({i + 1}) * {{
             width: fit-content !important;
        }}

        [CLASS_NAME] .stHorizontalBlock {{
            align-items: {vertical_align_items};
        }}
        """
                int_cols.append(1)
            else:
                int_cols.append(col)

        if additional_style:
            style += additional_style

        container = cls.container_with_style(key, style)
        return container.columns(int_cols)

    @classmethod
    def container_full_min_height(cls, key: str, additional_style: str = None):
        """Define a container with full min height.

        :param key: key
        :type key: str
        :return: _description_
        :rtype: _type_
        """
        # 8*2px of main padding
        # 16px of main row wrap (of a column)
        style = """
        [CLASS_NAME] {
            min-height: calc(100vh - 32px);
        }
        """

        if additional_style:
            style += additional_style

        return cls.container_with_style(key, style)

    @classmethod
    def full_width_dataframe_container(cls, key: str, additional_style: str = None):
        """Define a container for a dataframe that uses use_container_width=True.
        This prevent the dataframe to be too large and to create a horizontal scroll.
        The horizontal scroll of the dataframe is due to the resize absolute cursor.

        :param key: key
        :type key: str
        :return: _description_
        :rtype: _type_
        """
        style = """
        [CLASS_NAME] {
            padding-inline: 2px;
            box-sizing: border-box;
        }
        """

        if additional_style:
            style += additional_style

        container = cls.container_with_style(key, style)
        return container.columns(1)[0]

    @classmethod
    def container_with_style(cls, key: str, style: str):
        """Define a container with a custom style.
        Use [CLASS_NAME] to define the class name of the container, it will be replaced real css class.

        :param key: key
        :type key: str
        :param style: css style. Use [CLASS_NAME] to define the class name. Don't provide <style> tag
        :type style: str
        :return: _description_
        :rtype: _type_
        """
        css_class = StreamlitHelper.get_element_css_class(key)

        style = style.replace('[CLASS_NAME]', '.' + css_class)
        st.markdown(
            f"""
            <style>
                {style}
            </style>
            """,
            unsafe_allow_html=True
        )

        return st.container(key=key)

    @classmethod
    def grid_container(cls, nb_columns: int, cells: List[StreamlitGridCell],
                       key: str, row_height: str = 'auto',
                       gap: str = None):
        """
        Define a grid container with cells. All columns have the same width.

        :param nb_columns: number of columns
        :type nb_columns: int
        :param cells: list of StreamlitGridCell that define the cells width and height
        :type cells: List[StreamlitGridCell]
        :param key: key
        :type key: str
        :param row_height: height of the row as css value (auto, 1fr, 100px...), defaults to 'auto'
        :type row_height: str, optional
        :param gap: gap between cells as css value (1em, 10px...), defaults to None
        :type gap: str, optional
        :return: _description_
        :rtype: _type_
        """

        style = f"""
[CLASS_NAME] {{
  display: grid;
  grid-template-columns: repeat({nb_columns}, 1fr);
  grid-auto-rows: {row_height};
}}
"""
        if gap:
            style += f"""
[CLASS_NAME] {{
    grid-gap: {gap};
}}

/* Set cell to fill height */
[CLASS_NAME] [data-testid="stVerticalBlockBorderWrapper"] > div {{
    height: 100%;
}}
"""
        i = 1
        for cell in cells:
            child_class = StreamlitHelper.get_element_css_class(f'{key}_{i}')

            style += f"""
[CLASS_NAME] [data-testid="stVerticalBlockBorderWrapper"]:has(.{child_class}) {{
    grid-column: span {cell.col_span};
    grid-row: span {cell.row_span};
    border: solid black
}}
"""
            i += 1

        children = []
        with cls.container_with_style(key, style):
            i = 1
            for cell in cells:
                child_key = f'{key}_{i}'
                children.append(cls.container_with_style(child_key, cell.style))
                i += 1

        return tuple(children)

    @classmethod
    def exception_container(cls, key: str,
                            error_text: str = "An error occurred",
                            exception: BaseException = None):
        """ Define a container that display an error message and an exception if provided.
        The exception detail can be displayed in a popover.

        :param key: key
        :type key: str
        :param error_text: Error text to show the user, defaults to "An error occurred"
        :type error_text: str, optional
        :param exception: if provided, the user can view the detail, defaults to None
        :type exception: BaseException, optional
        """
        with cls.row_container(key, flow='row', vertical_align_items='center'):
            st.error(error_text)
            if exception:
                with st.popover('View details'):
                    st.exception(exception)

    @classmethod
    def fragment(cls, key: str):
        """ Decorator that works like st.fragment but catch exception and display
        them in an exception container.

        Use like this:
        ```
        @StreamlitContainers.fragment('my-key')
        def my_function():
            # code that can raise an exception
        ```

        :param key: key
        :type key: str
        """

        def decorator(func):
            @st.fragment
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    cls.exception_container(key,
                                            error_text=f"An error occurred: {str(e)}",
                                            exception=e)
            return wrapper

        return decorator
