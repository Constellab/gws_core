from collections.abc import Callable, Iterable
from typing import Any, Literal

import streamlit as st
from pandas import DataFrame
from streamlit.elements.arrow import ColumnConfigMappingInput, SelectionMode


def _select_by_coords(
    input_df: DataFrame, from_row_id: int, to_row_id: int, from_column_id: int, to_column_id: int
):
    return input_df.iloc[from_row_id:to_row_id, from_column_id:to_column_id]


def dataframe_paginated(
    dataframe: DataFrame,
    paginate_rows: bool = True,
    row_page_size_options: list[int] = None,
    paginate_columns: bool = False,
    column_page_size_options: list[int] = None,
    transformer: Callable[[Any], DataFrame] = None,
    width: int | None = None,
    height: int | None = None,
    hide_index: bool = False,
    column_order: Iterable[str] | None = None,
    column_config: ColumnConfigMappingInput | None = None,
    on_select: Literal["ignore", "rerun"] = "ignore",
    selection_mode: SelectionMode | Iterable[SelectionMode] = "multi-row",
    key: str = "dataframe_paginated",
) -> Any:
    """
    Paginate a dataframe in streamlit.
    Can only be used in a streamlit app.
    Import it like this: `from gws_streamlit_helper import dataframe_paginated`

    :param dataframe: dataframe to paginate. It only supports pandas dataframe.
    :type dataframe: DataFrame
    :param paginate_rows: whether to paginate rows, defaults to True
    :type paginate_rows: bool, optional
    :param row_page_size_options: list of page size available, defaults to [25, 50, 100]
    :type row_page_size_options: List[int], optional
    :param paginate_columns: whether to paginate columns, defaults to False
    :type paginate_columns: bool, optional
    :param column_page_size_options: list of page size available, defaults to row_page_size_options
    :type column_page_size_options: List[int], optional
    :param transformer: function to apply to the dataframe before displaying it (after pagination).
    Ex apply a style : `transformer = lambda df : df.style.format(thousands=" ", precision=1)`, defaults to None
    :type transformer: Callable[[DataFrame]], optional
    :param width: view st.dataframe width parameter, defaults to None
    :type width: int | None, optional
    :param height: view st.dataframe height parameter, defaults to None
    :type height: int | None, optional
    :param hide_index: view st.dataframe hide_index parameter, defaults to False
    :type hide_index: bool, optional
    :param column_order: view st.dataframe column_order parameter, defaults to None
    :type column_order: Iterable[str] | None, optional
    :param column_config: view st.dataframe column_config parameter, defaults to None
    :type column_config: ColumnConfigMappingInput | None, optional
    :param on_select: view st.dataframe on_select parameter, defaults to "ignore"
    :type on_select: Literal["ignore", "rerun"], optional
    :param selection_mode: view st.dataframe selection_mode parameter, defaults to "multi-row"
    :type selection_mode: SelectionMode | Iterable[SelectionMode], optional
    :param key: key for the dataframe, defaults to 'dataframe_paginated'
    :type key: str, optional
    :return: _description_
    :rtype: Any
    """

    if not isinstance(dataframe, DataFrame):
        raise ValueError(
            "dataframe must be a pandas DataFrame. If you want to apply a function like a style, please use the transformer parameter"
        )
    if row_page_size_options is None:
        row_page_size_options = [50, 100, 250]

    if column_page_size_options is None:
        column_page_size_options = row_page_size_options

    pagination = st.container(key=f"{key}_container")
    bottom_menu = st.columns((4, 1, 1))

    # handle row pagination
    from_row_id: int = 0
    to_row_id: int = len(dataframe)
    if paginate_rows:
        with bottom_menu[2]:
            page_size = st.selectbox(
                "Page Size", options=row_page_size_options, key=f"{key}_page_size"
            )
        with bottom_menu[1]:
            total_number_of_items = len(dataframe)
            total_pages = int(total_number_of_items / page_size) + int(
                bool(total_number_of_items % page_size)
            )
            current_page = st.number_input(
                "Page", min_value=1, max_value=total_pages, step=1, key=f"{key}_page"
            )
        with bottom_menu[0]:
            st.markdown(f"Page **{current_page}** of **{total_pages}** ")

        from_row_id = int((current_page - 1) * page_size)
        to_row_id = int(current_page * page_size)

    # handle column pagination
    from_column_id = 0
    to_column_id = len(dataframe.columns)
    if paginate_columns:
        with bottom_menu[2]:
            page_size = st.selectbox(
                "Column page Size", options=column_page_size_options, key=f"{key}_column_page_size"
            )
        with bottom_menu[1]:
            total_number_of_items = len(dataframe.columns)
            total_pages = int(total_number_of_items / page_size) + int(
                bool(total_number_of_items % page_size)
            )
            current_page = st.number_input(
                "Column page", min_value=1, max_value=total_pages, step=1, key=f"{key}_column_page"
            )
        with bottom_menu[0]:
            st.markdown(f"Column page **{current_page}** of **{total_pages}** ")

        from_column_id = int((current_page - 1) * page_size)
        to_column_id = int(current_page * page_size)

    pages = _select_by_coords(dataframe, from_row_id, to_row_id, from_column_id, to_column_id)

    if transformer is not None:
        pages = transformer(pages)
    return pagination.dataframe(
        pages,
        hide_index=hide_index,
        column_order=column_order,
        column_config=column_config,
        on_select=on_select,
        selection_mode=selection_mode,
        width=width or "stretch",
        height=height or "auto",
        key=f"{key}_dataframe",
    )
