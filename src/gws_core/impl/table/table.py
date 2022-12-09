# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, Dict, List, Literal, Union

import numpy as np
from pandas import DataFrame, Series
from pandas.api.types import (is_bool_dtype, is_float_dtype, is_integer_dtype,
                              is_string_dtype)

from gws_core.core.utils.logger import Logger
from gws_core.core.utils.utils import Utils
from gws_core.impl.table.helper.dataframe_helper import DataframeHelper
from gws_core.impl.table.table_axis_tags import TableAxisTags
from gws_core.impl.table.view.table_vulcano_plot_view import \
    TableVulcanoPlotView

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.r_field.dict_r_field import DictRField
from ...resource.r_field.primitive_r_field import StrRField
from ...resource.r_field.serializable_r_field import SerializableRField
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.view.view_decorator import view
from .data_frame_r_field import DataFrameRField
from .helper.dataframe_filter_helper import (DataframeFilterHelper,
                                             DataframeFilterName)
from .table_types import (AxisType, TableColumnType, TableHeaderInfo,
                          TableMeta, is_row_axis)
from .view.table_barplot_view import TableBarPlotView
from .view.table_boxplot_view import TableBoxPlotView
from .view.table_heatmap_view import TableHeatmapView
from .view.table_histogram_view import TableHistogramView
from .view.table_lineplot_2d_view import TableLinePlot2DView
from .view.table_scatterplot_2d_view import TableScatterPlot2DView
from .view.table_stacked_barplot_view import TableStackedBarPlotView
from .view.table_venn_diagram_view import TableVennDiagramView
from .view.table_view import TableView

ALLOWED_XLS_FILE_FORMATS = ['xlsx', 'xls']
ALLOWED_TXT_FILE_FORMATS = ['csv', 'tsv', 'tab', 'txt']
ALLOWED_FILE_FORMATS = [*ALLOWED_XLS_FILE_FORMATS, *ALLOWED_TXT_FILE_FORMATS]


@resource_decorator("Table", human_name="Table", short_description="2d excel like table")
class Table(Resource):
    """
    Main 2d table with named columns and named rows. It can also contains tags for each column and row.

    It has a lot of transformers to manipulate the data.

    It has a lot of chart views to visualize the data.

    """

    ALLOWED_DELIMITER = ["auto", "tab", "space", ",", ";"]
    DEFAULT_DELIMITER = "auto"
    DEFAULT_FILE_FORMAT = "csv"

    ALLOWED_XLS_FILE_FORMATS = ALLOWED_XLS_FILE_FORMATS
    ALLOWED_TXT_FILE_FORMATS = ALLOWED_TXT_FILE_FORMATS
    ALLOWED_FILE_FORMATS = ALLOWED_FILE_FORMATS

    COMMENT_CHAR = '#'

    _data: DataFrame = DataFrameRField()
    _meta: TableMeta = DictRField()

    _row_tags: TableAxisTags = SerializableRField(TableAxisTags)
    _column_tags: TableAxisTags = SerializableRField(TableAxisTags)
    comments: str = StrRField()

    def __init__(self, data: Union[DataFrame, np.ndarray, list] = None,
                 row_names: List[str] = None, column_names: List[str] = None,
                 row_tags: List[Dict[str, str]] = None, column_tags: List[Dict[str, str]] = None,
                 meta: TableMeta = None):
        super().__init__()
        self._set_data(data, row_names=row_names, column_names=column_names,
                       row_tags=row_tags, column_tags=column_tags, meta=meta)

    def _set_data(self, data: Union[DataFrame, np.ndarray] = None,
                  row_names=None, column_names=None,
                  row_tags: List[Dict[str, str]] = None, column_tags: List[Dict[str, str]] = None,
                  meta: TableMeta = None) -> 'Table':
        if data is None:
            data = DataFrame()
        else:
            if isinstance(data, Series):
                data = data.to_frame()
            if isinstance(data, DataFrame):
                # OK!
                pass
            elif isinstance(data, (np.ndarray, list)):
                data = DataFrame(data)
            else:
                raise BadRequestException(
                    "The data must be an instance of DataFrame or Numpy array")

            if (column_names is not None) and not isinstance(column_names, list):
                raise BadRequestException("The column_names must be an instance of list")
            if (row_names is not None) and not isinstance(row_names, list):
                raise BadRequestException("The row_names must be an instance of list")

            if column_names:
                data.columns = column_names
            data.columns = data.columns

            if row_names:
                data.index = row_names

        self._data = data

        if meta:
            # TODO remove meta on version 0.3.15
            Logger.warning("[Table] The meta data is deprecated. Use row_tags and column_tags instead.")
            self._set_tags(row_tags=meta.get("row_tags", None), column_tags=meta.get("column_tags", None))
        else:
            self._set_tags(row_tags=row_tags, column_tags=column_tags)

        return self

    def _set_tags(self, row_tags: List[Dict[str, str]] = None, column_tags: List[Dict[str, str]] = None):
        if row_tags:
            self.set_all_row_tags(row_tags)
        else:
            self.set_all_row_tags([{}] * self.nb_rows)

        if column_tags:
            self.set_all_column_tags(column_tags)
        else:
            self.set_all_column_tags([{}] * self.nb_columns)

    def get_meta(self) -> TableMeta:
        """Get a copy of the table meta data information

        :return: _description_
        :rtype: TableMeta
        """
        # TODO remove meta on version 0.3.15
        Logger.warning("[Table] The meta data is deprecated. Use row_tags and column_tags instead.")
        return {
            "row_tags": self.get_row_tags(),
            "column_tags": self.get_column_tags()
        }

    def add_row_tag(self, row_index: int, key: str, value: str) -> None:
        """
        Add a {key, value} tag to a row at a given index
        """

        self._row_tags.add_tag_at(row_index, key, value)

    def add_column_tag(self, column_index: int, key: str, value: str) -> None:
        """
        Add a {key, value} tag to a column at a given index
        """

        self._column_tags.add_tag_at(column_index, key, value)

    def set_comments(self, comments: str = ""):
        if not isinstance(comments, str):
            raise Exception("The comments must be a string")
        if comments and comments[0] != self.COMMENT_CHAR:
            comments = self.COMMENT_CHAR + comments
        self.comments = comments

    def set_all_row_tags(self, tags: List[Dict[str, str]]) -> None:
        if len(tags) != self.nb_rows:
            raise Exception("The length of tags must be equal to the number of rows")

        self._row_tags = TableAxisTags(tags)

    # TODO deprecated, to remove
    def set_all_rows_tags(self, tags: List[Dict[str, str]]) -> None:
        Logger.error("[Table] The set_all_rows_tags is deprecated. Use set_all_row_tags instead.")
        self.set_all_row_tags(tags)

    def set_all_column_tags(self, tags: List[Dict[str, str]]) -> None:
        if len(tags) != self.nb_columns:
            raise Exception("The length of tags must be equal to the number of columns")

        self._column_tags = TableAxisTags(tags)

    # TODO deprecated, to remove
    def set_all_columns_tags(self, tags: List[Dict[str, str]]) -> None:
        Logger.error("[Table] The set_all_columns_tags is deprecated. Use set_all_column_tags instead.")
        self.set_all_column_tags(tags)

    def get_data(self) -> DataFrame:
        return self._data.copy()

    @property
    def column_names(self) -> list:
        """
        Returns the column names of the Datatable.

        :return: The list of column names or `None` is no column names exist
        :rtype: list or None
        """

        try:
            return self._data.columns.values.tolist()
        except:
            return None

    def column_exists(self, name: str, case_sensitive: bool = True) -> bool:
        if case_sensitive:
            return name in self.column_names
        else:
            lower_names = [x.lower() for x in self.column_names]
            return name.lower() in lower_names

    def generate_new_column_name(self, name: str) -> str:
        """  Generates a column name that is unique in the Dataframe base on name.
        If the column name doesn't exist, return name, otherwise return name_1 or name_2, ...
        """
        return Utils.generate_unique_str_for_list(self.column_names, name)

    def get_column_data(self, column_name: str) -> List[Any]:
        """
        Returns the column data of the Dataframe with the given name.
        """
        return self._data[column_name].values.tolist()

    def get_column_as_dataframe(self, column_name: str, skip_nan=False) -> DataFrame:
        """
        Get a column as a dataframe
        """

        df = self._data[[column_name]]
        if skip_nan:
            df.dropna(inplace=True)
        return df

    def get_column_as_list(self, column_name: str, skip_nan=False) -> list:
        """
        Get a column as a list
        """

        dataframe = self.get_column_as_dataframe(column_name, skip_nan)
        return DataframeHelper.flatten_dataframe_by_column(dataframe)

    def add_column(self, name: str, data: Union[list, Series] = None, index: int = None):
        """ Add a new column to the Dataframe.
        :param column_name: name of the column
        :type column_name: str
        :param column_data: data for the column, must be the same length as other colums
        :type column_data: list
        :param column_index: index for the column, if none, the column is append to the end, defaults to None
        :type column_index: int, optional
        """

        if data is None:
            # use max 1 for special case when table is empty
            data = [None] * max(self.nb_rows, 1)

        if isinstance(data, Series):
            data = data.tolist()

        if not isinstance(data, list):
            raise BadRequestException("The column data must be a list")
        if self.nb_rows > 0 and len(data) != self.nb_rows:
            raise BadRequestException("The length of column data must be equal to the number of rows")
        if self.column_exists(name):
            raise BadRequestException(f"The column name `{name}` already exists")

        # if the table was empty, it will create new rows
        # so we need to create the row tags
        if self.nb_rows == 0:
            self._row_tags.insert_new_empty_tags(count=len(data))

        # insert columns
        if index is None:
            self._data[name] = data
        else:
            self._data.insert(index, name, data)

        self._column_tags.insert_new_empty_tags(index)

    def remove_column(self, column_name: str) -> None:
        """ Remove a column from the Dataframe.
        :param column_name: name of the column
        :type column_name: str
        """

        if not self.column_exists(column_name):
            raise BadRequestException(f"The column name `{column_name}` doesn't exist")

        pos = self.get_column_position_from_name(column_name)
        self._data.drop(columns=[column_name], inplace=True)
        self._column_tags.remove_tags_at(pos)

    def set_column_name(self, old_name: str, new_name: str) -> None:

        if not self.column_exists(old_name):
            raise BadRequestException(f"The column name `{old_name}` doesn't exist")
        if self.column_exists(new_name):
            raise BadRequestException(f"The column name `{new_name}` already exists")

        self._data.rename(columns={old_name: new_name}, inplace=True)

    def set_all_column_names(self, column_names: List[str]) -> None:

        if len(column_names) != self.nb_columns:
            raise BadRequestException("The length of column names must be equal to the number of columns")

        self._data.columns = column_names

    # def add_row(self, row_name: str = None, row_data: Union[list, Series] = None, row_index: int = None):
    #     """ Add a new row to the Dataframe.
    #     :param row_data: data for the row, must be the same length as other rows
    #     :type row_data: list
    #     :param row_index: index for the row, if none, the row is append to the end, defaults to None
    #     :type row_index: int, optional
    #     """

    #     if row_data is None:
    #         row_data = [None] * max(self.nb_columns, 1)

    #     if isinstance(row_data, Series):
    #         row_data = row_data.tolist()

    #     if not isinstance(row_data, list):
    #         raise BadRequestException("The row data must be a list")
    #     if self.nb_columns > 0 and len(row_data) != self.nb_columns:
    #         raise BadRequestException("The length of row data must be equal to the number of columns")
    #     if self.row_exists(row_name):
    #         raise BadRequestException(f"The row name `{row_name}` already exists")

    #     if row_index is None:
    #         row_index = self.nb_rows

    #     if row_name:
    #         self.set_row_name(row_index, row_name)

    #     self._data.loc[row_index] = row_data
    #     self.row_names

    #     self._row_tags.insert_new_empty_tags(row_index)

    def set_row_name(self, old_name: Any, new_name: str) -> None:
        """ Set the name of a row at a given index
        :param row_index: index of the row
        :type row_index: int
        :param name: name of the row
        :type name: str
        """

        if not self.row_exists(old_name):
            raise BadRequestException(f"The row name `{old_name}` does not exist")
        if self.row_exists(new_name):
            raise BadRequestException(f"The row name `{new_name}` already exists")

        self._data.rename(index={old_name: new_name}, inplace=True)

    def set_all_row_names(self, row_names: List[str]) -> None:

        if len(row_names) != self.nb_rows:
            raise BadRequestException("The length of row names must be equal to the number of rows")

        self._data.index = row_names

    def row_exists(self, name: str, case_sensitive: bool = True) -> bool:
        if case_sensitive:
            return name in self.row_names
        else:
            lower_names = [x.lower() for x in self.row_names]
            return name.lower() in lower_names

    def set_cell_value_at(self, row_index: int, column_index: int, value: Any):
        """ Set the value of a cell at a given index
        """
        self._data.iat[row_index, column_index] = value

    def get_cell_value_at(self, row_index: int, column_index: int) -> Any:
        """ Get the value of a cell at a given index
        """
        return self._data.iat[row_index, column_index]

    def get_tags(self, axis: AxisType) -> List[Dict[str, str]]:
        """
        Get tags
        """

        return self.get_row_tags() if is_row_axis(axis) else self.get_column_tags()

    def get_row_tags(self, from_index: int = None, to_index: int = None,
                     none_if_empty: bool = False,) -> List[Dict[str, str]]:
        return self._row_tags.get_tags_between(from_index, to_index, none_if_empty)

    def get_available_row_tags(self) -> Dict[str, List[str]]:
        """Get the complete list of row tags with list of values for each
        """
        return self._row_tags.get_available_tags()

    def get_row_names_by_positions(self, positions: List[int]) -> List[Union[str, int]]:
        """Function to retrieve the row names based on row positions
        """
        if not isinstance(positions, list):
            raise BadRequestException("The positions must be a list of integers")
        if not all(isinstance(x, int) for x in positions):
            raise BadRequestException("The positions must be a list of integers")
        # get the row names of the row positions
        return list(self._data.iloc[positions, :].index)

    def get_row_position_from_name(self, row_name: str) -> List[TableHeaderInfo]:
        return self._data.index.get_loc(row_name)

    def get_rows_info(self, from_index: int = None, to_index: int = None) -> List[TableHeaderInfo]:
        rows_info: List[TableHeaderInfo] = []
        for index, row in self._data.iterrows():
            rows_info.append(self.get_row_info(row.name))

        if from_index is not None or to_index is not None:
            rows_info = rows_info[from_index:to_index]
        return rows_info

    def get_row_info(self, row_name: str) -> TableHeaderInfo:
        row_position = self.get_row_position_from_name(row_name)
        return {
            "name": row_name,
            "tags": self._row_tags.get_tags_at(row_position)
        }

    def get_row_names(self, from_index: int = None, to_index: int = None) -> List[str]:
        """Get the row names
        """
        return self._data.index.tolist()[from_index:to_index]

    def get_column_tags(self, from_index: int = None, to_index: int = None,
                        none_if_empty: bool = False) -> List[Dict[str, str]]:

        return self._column_tags.get_tags_between(from_index, to_index, none_if_empty)

    def get_column_tag_by_name(self, column_name: str) -> Dict[str, str]:
        position = self.get_column_position_from_name(column_name)
        return self._column_tags.get_tags_at(position)

    def get_available_column_tags(self) -> Dict[str, List[str]]:
        """Get the complete list of column tags with list of values for each
        """
        return self._column_tags.get_available_tags()

    def get_column_names_by_positions(self, positions: List[int]) -> List[Union[str, int]]:
        """Function to retrieve the column names based on row positions
        """
        if not isinstance(positions, list):
            raise BadRequestException("The positions must be a list of integers")
        if not all(isinstance(x, int) for x in positions):
            raise BadRequestException("The positions must be a list of integers")
        # get the row names of the row positions
        return list(self._data.iloc[:, positions].columns)

    def get_column_position_from_name(self, column_name: str) -> int:
        return self._data.columns.get_loc(column_name)

    def get_columns_info(self, from_index: int = None, to_index: int = None) -> List[TableHeaderInfo]:
        column_infos: List[TableHeaderInfo] = []
        for column in self._data:
            column_infos.append(self.get_column_info(column))

        if from_index is not None or to_index is not None:
            column_infos = column_infos[from_index:to_index]
        return column_infos

    def get_column_info(self, column_name: str) -> TableHeaderInfo:
        column_position = self.get_column_position_from_name(column_name)

        return {
            "name": column_name,
            "type": self.get_column_type(column_name),
            "tags": self._column_tags.get_tags_at(column_position)
        }

    def get_column_names(self, from_index: int = None, to_index: int = None) -> List[str]:
        """Get the column names
        """
        return self._data.columns.tolist()[from_index:to_index]

    def get_column_type(self, column_name) -> TableColumnType:
        # get the type of the column
        column = self._data[column_name]
        if is_integer_dtype(column):
            return TableColumnType.INTEGER
        elif is_float_dtype(column):
            return TableColumnType.FLOAT
        elif is_bool_dtype(column):
            return TableColumnType.BOOLEAN
        elif is_string_dtype(column):
            return TableColumnType.STRING
        else:
            return TableColumnType.OBJECT

    def copy_column_tags(self, table: 'Table', from_index: int = None, to_index: int = None) -> None:
        self.set_all_column_tags(table.get_column_tags(from_index=from_index, to_index=to_index))

    def copy_row_tags(self, table: 'Table', from_index: int = None, to_index: int = None) -> None:
        self.set_all_row_tags(table.get_row_tags(from_index=from_index, to_index=to_index))

    def head(self, nrows=5) -> DataFrame:
        """
        Returns the first n rows for the columns ant targets.

        :param nrows: Number of rows
        :param nrows: int
        :return: The `panda.DataFrame` objects representing the n first rows of the `data`
        :rtype: pandas.DataFrame
        """

        return self._data.head(nrows)

    @property
    def is_vector(self) -> bool:
        return self.nb_rows == 1 or self.nb_columns == 1

    @property
    def is_column_vector(self) -> bool:
        return self.nb_columns == 1

    @property
    def is_row_vector(self) -> bool:
        return self.nb_rows == 1

    # -- N --

    @property
    def nb_columns(self) -> int:
        """
        Returns the number of columns.

        :return: The number of columns
        :rtype: int
        """

        return self._data.shape[1]

    @property
    def nb_rows(self) -> int:
        """
        Returns the number of rows.

        :return: The number of rows
        :rtype: int
        """

        return self._data.shape[0]

    # -- R --

    @property
    def row_names(self) -> list:
        """
        Returns the row names.

        :return: The list of row names
        :rtype: list
        """

        return self._data.index.values.tolist()

    # -- S --

    def select_by_row_positions(self, positions: List[int]) -> 'Table':
        row_names = self.get_row_names_by_positions(positions)
        return self.select_by_row_names([{"name": row_names}])

    def select_by_column_positions(self, positions: List[int]) -> 'Table':
        column_names = self.get_column_names_by_positions(positions)
        return self.select_by_column_names([{"name": column_names}])

    def select_by_row_names(self, filters: List[DataframeFilterName]) -> 'Table':
        data = DataframeFilterHelper.filter_by_axis_names(self._data, 'row', filters)

        return self.create_sub_table_filtered_by_rows(data)

    def select_by_column_names(self, filters: List[DataframeFilterName]) -> 'Table':
        data = DataframeFilterHelper.filter_by_axis_names(self._data, 'column', filters)

        return self.create_sub_table_filtered_by_columns(data)

    def select_by_coords(self, from_row_id: int, from_column_id: int, to_row_id: int, to_column_id: int) -> 'Table':
        """Create a new table from coords. It includes the to_row_id and to_column_id
        """
        data: DataFrame = self._data.iloc[from_row_id: to_row_id + 1,
                                          from_column_id: to_column_id + 1]

        # create a new table
        return self.create_sub_table(data, self.get_row_tags(from_index=from_row_id, to_index=to_row_id),
                                     self.get_column_tags(from_index=from_column_id, to_index=to_column_id))

    def select_by_row_tags(self, tags: List[dict]) -> 'Table':
        """
        Select table rows matching a list of tags

        Example of search tags are:

        - `tags = [ {"key1": "value1"} ]` to select rows having a tag `{"key1": "value1"}`
        - `tags = [ {"key1": "value1", "key2": "value2"} ]` to select rows having tags `{"key1": "value1"} AND {"key2": "value2"}`
        - `tags = [ {"key1": "value1"}, {"key2": "value2"} ]` to select rows having tags `{"key1": "value1"} OR {"key2": "value2"}`
        - `tags = [ {"key1": "value1", "key2": "value2"}, {"key3": "value3"} ]` to select rows having tags `({"key1": "value1"} AND {"key2": "value2"}) OR {"key2": "value2"}`
        - AND and OR logics can further be combined to perform complex selects

        :param tags: The of tags
        :param tags: List[dict]
        :return: The selected table
        :rtype: Table
        """

        return self.select_by_tags("index", tags)

    def select_by_column_tags(self, tags: List[dict]) -> 'Table':
        """
        Select table columns matching a list of tags

        Example of search tags are:

        - `tags = [ {"key1": "value1"} ]` to select columns having a tag `{"key1": "value1"}`
        - `tags = [ {"key1": "value1", "key2": "value2"} ]` to select columns having tags `{"key1": "value1"} AND {"key2": "value2"}`
        - `tags = [ {"key1": "value1"}, {"key2": "value2"} ]` to select columns having tags `{"key1": "value1"} OR {"key2": "value2"}`
        - `tags = [ {"key1": "value1", "key2": "value2"}, {"key3": "value3"} ]` to select columns having tags `({"key1": "value1"} AND {"key2": "value2"}) OR {"key2": "value2"}`
        - AND and OR logics can further be combined to perform complex selects

        :param tags: The of tags
        :param tags: List[dict]
        :return: The selected table
        :rtype: Table
        """
        return self.select_by_tags("columns", tags)

    def select_by_tags(self, axis: AxisType, tags: List[dict]) -> 'Table':
        positions = self._get_position_by_tags(axis, tags)

        return self.select_by_row_positions(positions) if is_row_axis(axis) else self.select_by_column_positions(
            positions)

    def filter_out_by_tags(self, axis: AxisType, tags: List[dict]) -> 'Table':
        # get position of the selected tags
        positions = self._get_position_by_tags(axis, tags)

        # get all the existing indexes
        all_indexes = list(range(self.nb_rows)) if is_row_axis(axis) else list(range(self.nb_columns))

        # get the indexes to keep by removing the selected ones from all index
        indexes_to_keep = [index for index in all_indexes if index not in positions]

        return self.select_by_row_positions(indexes_to_keep) if is_row_axis(axis) else self.select_by_column_positions(
            indexes_to_keep)

    def _get_position_by_tags(self, axis: AxisType, tags: List[dict]) -> List[int]:
        """ Return the position of the tags in the axis """
        if not isinstance(tags, list):
            raise BadRequestException("A list of tags is required")

        header_tags = self.get_tags(axis)
        position_union = []
        for tag in tags:
            position_instersect = []
            for key, value in tag.items():
                if not position_instersect:
                    position_instersect = [i for i, t in enumerate(header_tags) if t.get(key) == value]
                else:
                    pos = [i for i, t in enumerate(header_tags) if t.get(key) == value]
                    position_instersect = list(set(pos) & set(position_instersect))

                if len(position_instersect) == 0:
                    break

            position_union.extend(position_instersect)

        position_union = sorted(list(set(position_union)))
        return position_union

    def select_numeric_columns(self, drop_na: Literal['all', 'any'] = 'all') -> 'Table':
        """
        Select numeric columns.
        - if drop_na = 'all', then drops columns where all values are nan (similar to `DataFrame.drop_na(how=all|any)`)
        - if drop_na = 'any', then drop columns where any values are nan (similar to `DataFrame.drop_na(how=all|any)`)
        """

        data = self._data.select_dtypes([np.number])
        if drop_na:
            data = data.dropna(how="all")
        if data.shape[1] == self._data.shape[0]:
            return self

        column_tags = self.get_column_tags()
        selected_col_tags = [column_tags[i] for i, name in enumerate(self.column_names) if name in data.columns]

        return self.create_sub_table(data, self.get_row_tags(), selected_col_tags)

    # Selection by exclusion

    def filter_out_by_row_names(self, filters: List[DataframeFilterName]) -> 'Table':
        data = DataframeFilterHelper.filter_out_by_axis_names(self._data, 'row', filters)

        return self.create_sub_table_filtered_by_rows(data)

    def filter_out_by_column_names(self, filters: List[DataframeFilterName]) -> 'Table':
        data = DataframeFilterHelper.filter_out_by_axis_names(self._data, 'column', filters)

        return self.create_sub_table_filtered_by_columns(data)

    def create_sub_table_filtered_by_rows(self, filtered_df: DataFrame) -> 'Table':
        """
        Create a sub Table based on a subset Dataframe of this original table filtered by rows.
        It copies the tags of this table into the new table based on row names that matched between
        filtered_df and this dataframe.
        """

        positions = [self._data.index.get_loc(k) for k in filtered_df.index if k in self._data.index]

        # get the row tags for the filtered rows
        row_tags = self._row_tags.get_tags_at_indexes(positions)

        # create a new table
        return self.create_sub_table(filtered_df, row_tags, self.get_column_tags())

    def create_sub_table_filtered_by_columns(self, filtered_df: DataFrame) -> 'Table':
        """
        Create a sub Table based on a subset Dataframe of this original table filtered by columns
        It copies the tags of this table into the new table based on column names that matched between
        filtered_df and this dataframe.
        """

        positions = [self._data.columns.get_loc(k) for k in filtered_df.columns if k in self._data.columns]

        # get the column tags for the filtered columns
        column_tags = self._column_tags.get_tags_at_indexes(positions)

        # create a new table
        return self.create_sub_table(filtered_df, self.get_row_tags(), column_tags)

    def create_sub_table(self, dataframe: DataFrame,
                         row_tags: List[Dict[str, str]], column_tags: List[Dict[str, str]]) -> 'Table':
        """
        Create a new table from a dataframe and a meta
        """
        new_table: Table = self.clone()
        new_table._set_data(dataframe)
        new_table._set_tags(row_tags, column_tags)
        return new_table

    def __str__(self):
        return super().__str__() + "\n" + \
            "Table:\n" + \
            self._data.__str__()

    def equals(self, o: object) -> bool:
        if not isinstance(o, Table):
            return False

        return self._data.equals(o._data) and self._row_tags.equals(o._row_tags) and self._column_tags.equals(
            o._column_tags)

    def transpose(self) -> 'Table':
        return Table(
            data=self._data.T,
            row_names=self.column_names,
            column_names=self.row_names,
            row_tags=self.get_column_tags(),
            column_tags=self.get_row_tags()
        )

    def to_list(self) -> list:
        return self.to_numpy().tolist()

    def to_numpy(self) -> np.ndarray:
        return self._data.to_numpy()

    def to_dataframe(self) -> DataFrame:
        return self._data

    def to_csv(self) -> str:
        return self._data.to_csv()

    def to_json(self) -> dict:
        return self._data.to_json()

    def tail(self, nrows=5) -> DataFrame:
        """
        Returns the last n rows for the columns ant targets.

        :param nrows: Number of rows
        :param nrows: int
        :return: The `panda.DataFrame` objects representing the n first rows of the `data`
        :rtype: pandas.DataFrame
        """

        return self._data.tail(nrows)

    # -- V ---

    @view(view_type=TableView, default_view=True, human_name='Tabular', short_description='View as a table', specs={})
    def view_as_table(self, params: ConfigParams) -> TableView:
        """
        View as table
        """

        return TableView(self)

    ################################################# PLOT VIEW #################################################
    # Plot view are hidden because they are manually called by the ResourceTableService

    @view(view_type=TableLinePlot2DView, human_name='Line plot 2D', short_description='View columns as 2D-line plots', specs={}, hide=True)
    def view_as_line_plot_2d(self, params: ConfigParams) -> TableLinePlot2DView:
        """
        View columns as 2D-line plots
        """

        return TableLinePlot2DView(self)

    @view(view_type=TableScatterPlot2DView, human_name='Scatter plot 2D',
          short_description='View columns as 2D-scatter plots', specs={}, hide=True)
    def view_as_scatter_plot_2d(self, params: ConfigParams) -> TableScatterPlot2DView:
        """
        View one or several columns as 2D-line plots
        """

        return TableScatterPlot2DView(self)

    @view(view_type=TableVulcanoPlotView, human_name='Vulcano plot',
          short_description='View columns vulcano plot', specs={}, hide=True)
    def view_as_vulcano_plot(self, params: ConfigParams) -> TableVulcanoPlotView:
        return TableVulcanoPlotView(self)

    @view(view_type=TableBarPlotView, human_name='Bar plot', short_description='View columns as 2D-bar plots', specs={}, hide=True)
    def view_as_bar_plot(self, params: ConfigParams) -> TableBarPlotView:
        """
        View one or several columns as 2D-bar plots
        """

        return TableBarPlotView(self)

    @view(view_type=TableStackedBarPlotView, human_name='Stacked bar plot',
          short_description='View columns as 2D-stacked bar plots', specs={}, hide=True)
    def view_as_stacked_bar_plot(self, params: ConfigParams) -> TableStackedBarPlotView:
        """
        View one or several columns as 2D-stacked bar plots
        """

        return TableStackedBarPlotView(self)

    @view(view_type=TableHistogramView, human_name='Histogram', short_description='View columns as 2D-line plots', specs={}, hide=True)
    def view_as_histogram(self, params: ConfigParams) -> TableHistogramView:
        """
        View columns as 2D-line plots
        """

        return TableHistogramView(self)

    @view(view_type=TableBoxPlotView, human_name='Box plot', short_description='View columns as box plots', specs={}, hide=True)
    def view_as_box_plot(self, params: ConfigParams) -> TableBoxPlotView:
        """
        View one or several columns as box plots
        """

        return TableBoxPlotView(self)

    @view(view_type=TableHeatmapView, human_name='Heatmap', short_description='View table as heatmap', specs={}, hide=True)
    def view_as_heatmap(self, params: ConfigParams) -> TableHeatmapView:
        """
        View the table as heatmap
        """

        return TableHeatmapView(self)

    @view(view_type=TableVennDiagramView, human_name='VennDiagram', short_description='View table as Venn diagram', specs={}, hide=True)
    def view_as_venn_diagram(self, params: ConfigParams) -> TableHeatmapView:
        """
        View the table as Venn diagram
        """

        return TableVennDiagramView(self)

    # @view(view_type=LinePlot3DView, human_name='LinePlot3D', short_description='View columns as 3D-line plots', specs={})
    # def view_as_line_plot_3d(self, params: ConfigParams) -> LinePlot3DView:
    #     """
    #     View columns as 3D-line plots
    #     """

    #     return LinePlot3DView(self)

    # @view(view_type=TableScatterPlot3DView, human_name='ScatterPlot3D', short_description='View columns as 3D-scatter plots', specs={})
    # def view_as_scatter_plot_3d(self, params: ConfigParams) -> TableScatterPlot3DView:
    #     """
    #     View columns as 3D-scatter plots
    #     """

    #     return TableScatterPlot3DView(self)

    ############################## CLASS METHODS ###########################
    @classmethod
    def from_dict(cls, data: dict, orient='index', dtype=None, columns=None) -> 'Table':
        dataframe = DataFrame.from_dict(data, orient, dtype, columns)
        res = cls(data=dataframe)
        return res
