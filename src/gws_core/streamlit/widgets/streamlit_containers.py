from typing import List, Literal

import streamlit as st

from .streamlit_helper import StreamlitHelper


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
                      vertical_align_items: Literal['start', 'center', 'end'] = 'start',
                      additional_style: str = None):
        """Define a row container, element inside a in a row (like buttons, text...)

        :param key: key
        :type key: str
        :param flow: flex-flow style, defaults to 'row wrap'
        :type flow: Literal[&#39;row&#39;, &#39;row wrap&#39;], optional
        :param align_items: vertical align-items style, defaults to 'start'
        :type align_items: Literal[&#39;start&#39;, &#39;center&#39;, &#39;end&#39;], optional
        :return: _description_
        :rtype: _type_
        """
        style = f"""
            [CLASS_NAME] {{
                flex-flow: {flow};
                align-items: {vertical_align_items};
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
                                 additional_style: str = None):
        """Define columns that also support fit content width.

        :param key: key
        :type key: str
        :param cols: list of columns width. Use 'fit-content' to define a column with fit content width
        :type cols: List[int | Literal[&#39;fit-content&#39;]]
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
