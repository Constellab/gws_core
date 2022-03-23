# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import copy
from typing import Dict, List, Literal, Union

import numpy as np
from pandas import DataFrame, Series

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.r_field import DictRField
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from .data_frame_r_field import DataFrameRField
from .view.table_barplot_view import TableBarPlotView
from .view.table_boxplot_view import TableBoxPlotView
from .view.table_heatmap_view import TableHeatmapView
from .view.table_histogram_view import TableHistogramView
from .view.table_lineplot_2d_view import TableLinePlot2DView
from .view.table_scatterplot_2d_view import TableScatterPlot2DView
from .view.table_stacked_barplot_view import TableStackedBarPlotView
from .view.table_venn_diagram_view import TableVennDiagramView
from .view.table_view import TableView

ALLOWED_DELIMITER = ["auto", "tab", "space", ",", ";"]
DEFAULT_DELIMITER = "auto"
DEFAULT_FILE_FORMAT = ".csv"
ALLOWED_XLS_FILE_FORMATS = ['.xlsx', '.xls']
ALLOWED_TXT_FILE_FORMATS = ['.csv', '.tsv', '.tab', '.txt']
ALLOWED_FILE_FORMATS = [*ALLOWED_XLS_FILE_FORMATS, *ALLOWED_TXT_FILE_FORMATS]

NUMERICAL_TAG_TYPE = "numerical"
CATEGORICAL_TAG_TYPE = "categorical"
ALLOWED_TAG_TYPES = [CATEGORICAL_TAG_TYPE, NUMERICAL_TAG_TYPE]


@resource_decorator("Table")
class Table(Resource):

    ALLOWED_DELIMITER = ALLOWED_DELIMITER
    DEFAULT_DELIMITER = DEFAULT_DELIMITER
    DEFAULT_FILE_FORMAT = DEFAULT_FILE_FORMAT
    ALLOWED_FILE_FORMATS = ALLOWED_FILE_FORMATS

    ALLOWED_XLS_FILE_FORMATS = ALLOWED_XLS_FILE_FORMATS
    ALLOWED_TXT_FILE_FORMATS = ALLOWED_TXT_FILE_FORMATS

    NUMERICAL_TAG_TYPE = NUMERICAL_TAG_TYPE
    CATEGORICAL_TAG_TYPE = CATEGORICAL_TAG_TYPE
    ALLOWED_TAG_TYPES = ALLOWED_TAG_TYPES

    _data: DataFrame = DataFrameRField()
    _meta: Dict = DictRField()

    def __init__(self, data: Union[DataFrame, np.ndarray, list] = None,
                 row_names=None, column_names=None,  meta: List = None):
        super().__init__()
        self._set_data(data, row_names=row_names, column_names=column_names, meta=meta)

    def _set_data(self, data: Union[DataFrame, np.ndarray] = None,
                  row_names=None, column_names=None,  meta=None) -> 'Table':
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
            data.columns = data.columns.map(str)

            if row_names:
                data.index = row_names

        self._data = data
        self._set_meta(meta)
        return self

    def _set_meta(self, meta: Dict = None):
        if meta is None:
            meta = {
                "row_tags": [{}] * self.nb_rows,
                "column_tags": [{}] * self.nb_columns,
                "row_tag_types": {},
                "column_tag_types": {},
            }
        else:
            if "row_tags" not in meta:
                meta["row_tags"] = [{}] * self.nb_rows
            if "column_tags" not in meta:
                meta["column_tags"] = [{}] * self.nb_columns
            if len(meta["row_tags"]) != self._data.shape[0]:
                raise BadRequestException("The length of row_tags must be equal to the number of rows")
            if len(meta["column_tags"]) != self._data.shape[1]:
                raise BadRequestException("The length of column_tags must be equal to the number of columns")

        self._meta = meta

    def _add_tag(
            self, axis, index: int, key: str, value: Union[str, int, float],
            type: Literal['categorical', 'numerical'] = 'categorical'):
        if axis not in ["row", "column"]:
            raise BadRequestException("The index must be an integer")
        if not isinstance(index, int):
            raise BadRequestException("The index must be an integer")
        if not isinstance(key, str):
            raise BadRequestException("The tag key must be a string")
        if not isinstance(value, (str, int, float)):
            raise BadRequestException("The tag value must be a string, int or float")
        if type not in self.ALLOWED_TAG_TYPES:
            raise BadRequestException(f"Invalid tag type '{type}'. The tag type must be in {self.ALLOWED_TAG_TYPES}")

        key = str(key)
        value = str(value)

        self._meta[axis + "_tags"][index][key] = value
        if key not in self._meta[axis + "_tag_types"]:
            self._meta[axis + "_tag_types"][key] = type
        else:
            if self._meta[axis + "_tag_types"][key] != type:
                raise BadRequestException(f"Tag '{key}' already exists with a different type")

    def add_row_tag(
            self, row_index: int, key: str, value: Union[str, int, float],
            type: Literal['categorical', 'numerical'] = 'categorical'):
        """
        Add a {key, value} tag to a row at a given index

        :param row_index: The row index
        :param row_index: int
        :param key: The tag key
        :param key: str
        :param value: The tag value
        :param value: str, int, float
        """

        self._add_tag("row", row_index, key, value, type=type)

    def add_column_tag(
            self, column_index: int, key: str, value: Union[str, int, float],
            type: Literal['categorical', 'numerical'] = 'categorical'):
        """
        Add a {key, value} tag to a column at a given index

        :param column_index: The column index
        :param column_index: int
        :param key: The tag key
        :param key: str
        :param value: The tag value
        :param value: str, int, float
        """

        self._add_tag("column", column_index, key, value, type=type)

    def convert_row_tags_to_dummy_target_matrix(self, key: str) -> DataFrame:
        tags = self.get_row_tags()
        targets = [tag[key] for tag in tags]
        labels = sorted(list(set(targets)))
        nb_labels = len(labels)
        nb_instances = len(targets)
        data = np.zeros(shape=(nb_instances, nb_labels))
        for i in range(0, nb_instances):
            current_label = targets[i]
            idx = labels.index(current_label)
            data[i][idx] = 1.0

        return DataFrame(data=data, index=targets, columns=labels)

    def set_row_tags(self, tags: list):
        if not isinstance(tags, list):
            raise BadRequestException("The tags must be a list")
        if len(tags) != self._data.shape[0]:
            raise BadRequestException("The length of tags must be equal to the number of rows")

        self._meta["row_tags"] = self.clean_tags(tags)

    def set_row_tag_types(self, types: dict):
        current_row_tags = self.get_row_tags()
        current_row_tag_types = self.get_row_tag_types()
        for k, t in types.items():
            if k not in current_row_tag_types:
                raise BadRequestException(f"The tag `{k}` does not exist")
            else:
                if v not in self.ALLOWED_TAG_TYPES:
                    raise BadRequestException(f"Invalid tag type '{v}'. The tag type in {self.ALLOWED_TAG_TYPES}")
                current_row_tag_types[k] = v

        self._meta["row_tag_types"] = current_row_tag_types

    def set_column_tags(self, tags: list):
        if not isinstance(tags, list):
            raise BadRequestException("The tags must be a list")
        if len(tags) != self._data.shape[1]:
            raise BadRequestException("The length of tags must be equal to the number of columns")

        self._meta["column_tags"] = self.clean_tags(tags)

    def set_column_tag_types(self, types: dict):
        current_column_tag_types = self.get_column_tag_types()
        for k, t in types.items():
            if k not in current_column_tag_types:
                raise BadRequestException(f"The tag `{k}` does not exist")
            else:
                if t not in self.ALLOWED_TAG_TYPES:
                    raise BadRequestException(
                        f"Invalid tag type '{t}'. The tag type must be in {self.ALLOWED_TAG_TYPES}")
                current_column_tag_types[k] = v

        self._meta["column_tag_types"] = current_column_tag_types

    def get_data(self):
        return self._data

    # -- C --

    @staticmethod
    def clean_tags(tags):
        try:
            return [{str(k): str(v) for k, v in t.items()} for t in tags]
        except:
            raise BadRequestException("The tags are not valid. Please check")

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

    def column_exists(self, name, case_sensitive=True) -> bool:
        if case_sensitive:
            return name in self.column_names
        else:
            lower_names = [x.lower() for x in self.column_names]
            return name.lower() in lower_names

    # -- F --

    @classmethod
    def from_dict(cls, data: dict, orient='index', dtype=None, columns=None) -> 'Table':
        dataframe = DataFrame.from_dict(data, orient, dtype, columns)
        res = cls(data=dataframe)
        return res

    # -- G --

    def get_column(self, column_name: str, rtype='list', skip_nan=False) -> Union['DataFrame', list]:
        if rtype == 'list':
            df = self._data[column_name]
            if skip_nan:
                df.dropna(inplace=True)
            return df.values.tolist()
        else:
            df = self._data[[column_name]]
            if skip_nan:
                df.dropna(inplace=True)
            return df

    def get_meta(self):
        return self._meta

    def get_row_tags(self, none_if_empty: bool = False,
                     from_index: int = None, to_index: int = None) -> List[Dict[str, str]]:
        tags = self._meta["row_tags"]
        are_tags_empty = [len(t) == 0 for t in tags]
        if all(are_tags_empty) and none_if_empty:
            return None

        if from_index is not None and to_index is not None:
            return tags[from_index:to_index]

        return tags

    def get_row_tag_types(self):
        return self._meta["row_tag_types"]

    def get_column_tags(self, none_if_empty: bool = False):
        tags = self._meta["column_tags"]
        are_tags_empty = [len(t) == 0 for t in tags]
        if all(are_tags_empty) and none_if_empty:
            return None
        else:
            return tags

    def get_column_tag_types(self):
        return self._meta["column_tag_types"]

    # -- H --

    def head(self, nrows=5) -> DataFrame:
        """
        Returns the first n rows for the columns ant targets.

        :param nrows: Number of rows
        :param nrows: int
        :return: The `panda.DataFrame` objects representing the n first rows of the `data`
        :rtype: pandas.DataFrame
        """

        return self._data.head(nrows)

    # -- I --

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
        if not isinstance(positions, list):
            raise BadRequestException("The positions must be a list of integers")
        if not all(isinstance(x, int) for x in positions):
            raise BadRequestException("The positions must be a list of integers")
        data = self._data.iloc[positions, :]
        meta = copy.deepcopy(self._meta)
        if "row_tags" in self._meta:
            meta["row_tags"] = [meta["row_tags"][k] for k in positions]
        cls = type(self)
        return cls(data=data, meta=meta)

    def select_by_column_positions(self, positions: List[int]) -> 'Table':
        if not isinstance(positions, list):
            raise BadRequestException("The positions must be a list of integers")
        if not all(isinstance(x, int) for x in positions):
            raise BadRequestException("The positions must be a list of integers")
        data = self._data.iloc[:, positions]
        meta = copy.deepcopy(self._meta)
        if "column_tags" in self._meta:
            meta["column_tags"] = [meta["column_tags"][k] for k in positions]
        cls = type(self)
        return cls(data=data, meta=meta)

    def select_by_row_names(self, names: List[str], use_regex=False) -> 'Table':
        if not isinstance(names, list):
            raise BadRequestException("The names must be a list of strings")
        if not all(isinstance(x, str) for x in names):
            raise BadRequestException("The names must be a list of strings")
        if use_regex:
            regex = "(" + ")|(".join(names) + ")"
            data = self._data.filter(regex=regex, axis=0)
        else:
            data = self._data.filter(items=names, axis=0)
        positions = [self._data.index.get_loc(k) for k in self._data.index if k in data.index]
        meta = copy.deepcopy(self._meta)
        if "row_tags" in self._meta:
            meta["row_tags"] = [meta["row_tags"][k] for k in positions]
        cls = type(self)
        return cls(data=data, meta=meta)

    def select_by_column_names(self, names: List[str], use_regex=False) -> 'Table':
        if not isinstance(names, list):
            raise BadRequestException("The names must be a list of strings")
        if not all(isinstance(x, str) for x in names):
            raise BadRequestException("The names must be a list of strings")
        if use_regex:
            regex = "(" + ")|(".join(names) + ")"
            data = self._data.filter(regex=regex, axis=1)
        else:
            data = self._data.filter(items=names, axis=1)
        positions = [self._data.columns.get_loc(k) for k in self._data.columns if k in data.columns]
        meta = copy.deepcopy(self._meta)
        if "column_tags" in self._meta:
            meta["column_tags"] = [meta["column_tags"][k] for k in positions]
        cls = type(self)
        return cls(data=data, meta=meta)

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

        if not isinstance(tags, list):
            raise BadRequestException("A list of tags is required")

        row_tags = self.get_row_tags()
        position_union = []
        for tag in tags:
            position_instersect = []
            for key, value in tag.items():
                if not position_instersect:
                    position_instersect = [i for i, t in enumerate(row_tags) if t.get(key) == value]
                else:
                    pos = [i for i, t in enumerate(row_tags) if t.get(key) == value]
                    position_instersect = list(set(pos) & set(position_instersect))

            position_union.extend(position_instersect)

        position_union = sorted(list(set(position_union)))
        return self.select_by_row_positions(position_union)

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

        if not isinstance(tags, list):
            raise BadRequestException("A list of tags is required")

        column_tags = self.get_column_tags()
        position_union = []
        for tag in tags:
            position_instersect = []
            for key, value in tag.items():
                if not position_instersect:
                    position_instersect = [i for i, t in enumerate(column_tags) if t.get(key) == value]
                else:
                    pos = [i for i, t in enumerate(column_tags) if t.get(key) == value]
                    position_instersect = list(set(pos) & set(position_instersect))

            position_union.extend(position_instersect)

        position_union = sorted(list(set(position_union)))
        return self.select_by_column_positions(position_union)

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
        table = Table(data=data)
        table.set_row_tags(self.get_row_tags())
        table.set_column_tags(selected_col_tags)
        return table

    def __str__(self):
        return super().__str__() + "\n" + \
            "Table:\n" + \
            self._data.__str__()

    # -- T --

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
    # Plot view are hidden because they are manually called by the front
    # /!\ DO NOT CHANGE THE FUNCTION NAMES OF THESES HIDDEN VIEWS /!\

    @view(view_type=TableLinePlot2DView, human_name='Line plot 2D', short_description='View columns as 2D-line plots', specs={}, hide=True)
    def view_as_line_plot_2d(self, params: ConfigParams) -> TableLinePlot2DView:
        """
        View columns as 2D-line plots
        """

        return TableLinePlot2DView(self)

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

    @view(view_type=TableScatterPlot2DView, human_name='Scatter plot 2D',
          short_description='View columns as 2D-scatter plots', specs={}, hide=True)
    def view_as_scatter_plot_2d(self, params: ConfigParams) -> TableScatterPlot2DView:
        """
        View one or several columns as 2D-line plots
        """

        return TableScatterPlot2DView(self)

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
