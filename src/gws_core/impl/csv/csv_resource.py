# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pathlib import Path
from typing import Union

import numpy as np
import pandas
from pandas import DataFrame

from ...core.exception.exceptions import BadRequestException
from ...resource.resource import Resource, SerializedResourceData
from ...resource.resource_decorator import ResourceDecorator


@ResourceDecorator("CSVTable")
class CSVTable(Resource):

    table: DataFrame

    def serialize_data(self) -> SerializedResourceData:
        return self.table.to_dict()

    def deserialize_data(self, data: SerializedResourceData) -> None:
        self.set_data(DataFrame.from_dict(data=data))

    def set_data(self, table: Union[DataFrame, np.ndarray] = None,
                 column_names=None, row_names=None) -> 'CSVTable':
        if table is None:
            table = DataFrame()
        else:
            if isinstance(table, DataFrame):
                # OK!
                pass
            elif isinstance(table, (np.ndarray, list)):
                table = DataFrame(table)
                if column_names:
                    table.columns = column_names
                if row_names:
                    table.index = row_names
            else:
                raise BadRequestException(
                    "The table must be an instance of DataFrame or Numpy array")

        self.table = table
        return self

    # -- C --

    @property
    def column_names(self) -> list:
        """
        Returns the column names of the Datatable.

        :return: The list of column names or `None` is no column names exist
        :rtype: list or None
        """

        try:
            return self.table.columns.values.tolist()
        except Exception as _:
            return None

    def column_exists(self, name, case_sensitive=True) -> bool:
        if case_sensitive:
            return name in self.column_names
        else:
            lower_names = [x.lower() for x in self.column_names]
            return name.lower() in lower_names

    # -- D --

    # -- E --

    def export(
            self, file_path: str, delimiter: str = "\t", header: bool = True, index: bool = True, file_format: str = None, **
            kwargs):
        """
        Export to a repository

        :param file_path: The destination file path
        :type file_path: File
        """

        file_extension = Path(file_path).suffix
        if file_extension in [".xls", ".xlsx"] or file_format in [".xls", ".xlsx"]:
            self.table.to_excel(file_path)
        elif file_extension in [".csv", ".tsv", ".txt", ".tab"] or file_format in [".csv", ".tsv", ".txt", ".tab"]:
            self.table.to_csv(
                file_path,
                sep=delimiter,
                index=index
            )
        else:
            raise BadRequestException(
                "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")

    # -- F --

    @classmethod
    def from_dict(cls, table: dict, orient='index', dtype=None, columns=None) -> 'CSVTable':
        df = DataFrame.from_dict(table, orient, dtype, columns)
        return cls(table=df)

    # -- G --

    def get_column(self, column_name: str, rtype='list') -> Union['DataFrame', list]:
        if rtype == 'list':
            return list(self.table[column_name].values)
        else:
            return self.table[[column_name]]

    # -- H --

    def head(self, n=5) -> DataFrame:
        """
        Returns the first n rows for the columns ant targets.

        :param n: Number of rows
        :param n: int
        :return: The `panda.DataFrame` objects representing the n first rows of the `table`
        :rtype: pandas.DataFrame
        """

        return self.table.head(n)

    # -- I --

    @classmethod
    def import_resource(cls, file_path: str, delimiter: str = "\t", header=0, index_col=None, file_format: str = None, **
                        kwargs) -> 'CSVTable':
        """
        Import from a repository

        :param file_path: The source file path
        :type file_path: File
        :returns: the parsed data
        :rtype any
        """

        file_extension = Path(file_path).suffix
        if file_extension in [".xls", ".xlsx"] or file_format in [".xls", ".xlsx"]:
            df = pandas.read_excel(file_path)
        elif file_extension in [".csv", ".tsv", ".txt", ".tab"] or file_format in [".csv", ".tsv", ".txt", ".tab"]:
            df = pandas.read_table(
                file_path,
                sep=delimiter,
                header=header,
                index_col=index_col
            )
        else:
            raise BadRequestException(
                "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")
        return cls().set_data(table=df)

    # -- N --

    @property
    def nb_columns(self) -> int:
        """
        Returns the number of columns.

        :return: The number of columns
        :rtype: int
        """

        return self.table.shape[1]

    @property
    def nb_rows(self) -> int:
        """
        Returns the number of rows.

        :return: The number of rows
        :rtype: int
        """

        return self.table.shape[0]

    # -- R --

    @property
    def row_names(self) -> list:
        """
        Returns the row names.

        :return: The list of row names
        :rtype: list
        """

        return self.table.index.values.tolist()

    def _view__as_csv(self, **kwargs):
        """
        Renders the model as a JSON string or dictionnary. This method is used by :class:`ViewModel` to create view rendering.

        :param kwargs: Parameters passed to the method :meth:`to_json`.
        :type kwargs: `dict`
        :return: The view representation
        :rtype: `dict`, `str`
        """

        return self.to_csv(stringify=True, **kwargs)

    def __str__(self):
        return self.table.__str__()

    def to_table(self):
        return self.table

    def to_csv(self, **kwargs):
        return self.table.to_csv()

     # -- T --
    def to_json(self, **kwargs) -> dict:
        return self.table.to_json()

    # -- V ---
