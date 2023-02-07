# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List

from pandas import DataFrame

from .....core.exception.exceptions import BadRequestException
from ....table.table import Table

# ####################################################################
#
# TableRowAnnotatorHelper class
#
# ####################################################################


class TableAnnotatorHelper():
    """
    TableRowAnnotatorHelper

    Annotate the rows of a `sample_table` using information from a `metadata_table`.
    * all the row values of the reference column of the `sample_table` are matched against the `ids` of the `metadata_table`.
    * if an `id` matches against a reference value of the `sample_table`, the corresponding row of the `sample_table` is taggeg with the metadata given by the `id`.
    """

    @classmethod
    def annotate_rows(cls, table: Table, metadata_table: Table,
                      table_ref_column: str = None, metadata_table_ref_column: str = None) -> Table:
        """
        Annotate the rows of a `table` using information from a `metadata_table`.
        All the row values of the reference column of the `table` are matched against the `ids` of the `metadata_table`.
        If an `id` matches against a reference value of the `table`, the corresponding row of the `table` is tagged with the metadata given by the `id`.

        :param table: the table to annotate
        :type table: Table
        :param metadata_table: the metadata table
        :type metadata_table: Table
        :param table_ref_column: ref column of the table to match against the metadata table
                                 If None or empty, the row names are used, defaults to None
        :type table_ref_column: str, optional
        :param metadata_table_ref_column: ref column of the metadata table to match against the table
                                         If None or empty, the row names are used, defaults to None
        :type metadata_table_ref_column: str, optional
        :raises BadRequestException: _description_
        :return: _description_
        :rtype: Table
        """

        # get the list of ids to match against the metadata table
        # from the row name or from the reference column
        table_ids: List[str]
        if table_ref_column:
            if not table.column_exists(table_ref_column):
                raise BadRequestException(f"The column '{table_ref_column}' does not exist in sample table")
            table_ids = table.get_column_data(table_ref_column)
            # convert each value to string
            table_ids = [str(id_) for id_ in table_ids]
        else:
            # use the index
            table_ids = table.get_row_names()

        metadata_tags: Dict[str, Dict[str, Any]] = cls._get_metadata_tags(metadata_table, metadata_table_ref_column)

        # for each id in the table, get the corresponding metadata tags
        tags = [metadata_tags.get(id_, {}) for id_ in table_ids]
        table.set_all_row_tags(tags)
        return table

    @classmethod
    def annotate_columns(cls, table: Table, metadata_table: Table,
                         table_ref_row: str = None, metadata_table_ref_column: str = None) -> Table:
        """
        Annotate the columns of a `table` using information from a `metadata_table`.
        All the column values of the reference row of the `table` are matched against the `ids` of the `metadata_table`.
        If an `id` matches against a reference value of the `table`, the corresponding column of the `table` is tagged with the metadata given by the `id`.


        :param table: the table to annotate
        :type table: Table
        :param metadata_table: the metadata table
        :type metadata_table: MetadataTable
        :param table_ref_row: ref row of the table to match against the metadata table
                              If None or empty, the column names are used, defaults to None
        :type table_ref_row: str, optional
        :param metadata_table_ref_column: ref column of the metadata table to match against the table
                                          If None or empty, the row names are used, defaults to None
        :type metadata_table_ref_column: str, optional
        :raises BadRequestException: _description_
        :return: _description_
        :rtype: Table
        """

        # get the list of ids to match against the metadata table
        # from the column name or from the reference row
        table_ids: List[str]
        if table_ref_row:
            if not table.row_exists(table_ref_row):
                raise BadRequestException(f"The column '{table_ref_row}' does not exist in sample table")
            table_ids = table.get_row_data(table_ref_row)
            # convert each value to string
            table_ids = [str(id_) for id_ in table_ids]
        else:
            # use the index
            table_ids = table.get_column_names()

        metadata_tags: Dict[str, Dict[str, Any]] = cls._get_metadata_tags(metadata_table, metadata_table_ref_column)

        # for each id in the table, get the corresponding metadata tags
        tags = [metadata_tags.get(id_, {}) for id_ in table_ids]
        table.set_all_column_tags(tags)
        return table

    @classmethod
    def _get_metadata_tags(cls, metadata_table: Table, ref_column: str = None) -> Dict[str, Dict[str, Any]]:
        """Return the metadata table as dict of tags where key = id and value = tags for the id
        """
        dataframe: DataFrame
        if ref_column:
            if not metadata_table.column_exists(ref_column):
                raise BadRequestException(f"The column '{ref_column}' does not exist in metadata table")
            # set the ref column as index name for the dataframe
            dataframe = metadata_table.get_data().set_index(ref_column)
        else:
            # use the index
            dataframe = metadata_table.get_data()

        # dataframe as dict of tags where key = id and value = tags for the id
        return dataframe.to_dict('index')
