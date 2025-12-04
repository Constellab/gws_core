from typing import Any, Dict, List

from pandas import DataFrame

from .....core.exception.exceptions import BadRequestException
from ....table.table import Table

# ####################################################################
#
# TableRowAnnotatorHelper class
#
# ####################################################################


class TableAnnotatorHelper:
    """
    TableRowAnnotatorHelper

    Annotate the rows of a `sample_table` using information from a `metadata_table`.
    * all the row values of the reference column of the `sample_table` are matched against the `ids` of the `metadata_table`.
    * if an `id` matches against a reference value of the `sample_table`, the corresponding row of the `sample_table` is taggeg with the metadata given by the `id`.
    """

    @classmethod
    def annotate_rows(
        cls,
        table: Table,
        metadata_table: Table,
        table_ref_column: str = None,
        metadata_table_ref_column: str = None,
        use_table_row_names_as_ref: bool = False,
        use_metadata_row_names_as_ref: bool = False,
    ) -> Table:
        """
        Annotate the rows of a `table` using information from a `metadata_table`.
        All the row values of the reference column of the `table` are matched against the `ids` of the `metadata_table`.
        If an `id` matches against a reference value of the `table`, the corresponding row of the `table` is tagged with the metadata given by the `id`.

        :param table: the table to annotate
        :type table: Table
        :param metadata_table: the metadata table
        :type metadata_table: Table
        :param table_ref_column: ref column of the table to match against the metadata table
                                 If None or empty, the first column is used, defaults to None
        :type table_ref_column: str, optional
        :param metadata_table_ref_column: ref column of the metadata table to match against the table
                                         If None or empty, the first column is used, defaults to None
        :type metadata_table_ref_column: str, optional
        :param use_table_index_as_ref: use the row names of the table as reference, if true the parameter table_ref_column is ignored, defaults to False
        :type use_table_index_as_ref: bool, optional
        :param use_metadata_index_as_ref: use the row names of the metadata table as reference, if true the parameter metadata_table_ref_column is ignored, defaults to False
        :type use_metadata_index_as_ref: bool, optional
        :raises BadRequestException: _description_
        :return: _description_
        :rtype: Table
        """

        # get the list of ids to match against the metadata table
        # from the row name or from the reference column
        table_ids: List[str]

        if use_table_row_names_as_ref:
            # use the index
            table_ids = table.get_row_names()
        elif table_ref_column:
            if not table.column_exists(table_ref_column):
                raise BadRequestException(
                    f"The column '{table_ref_column}' does not exist in table"
                )

            # use the column values as reference
            table_ids = table.get_column_data(table_ref_column)
        else:
            # use the first column as reference
            table_ids = table.get_column_data(table.get_column_names()[0])

        # convert each value to string
        table_ids = [str(id_) for id_ in table_ids]
        metadata_tags: Dict[str, Dict[str, str]] = cls._get_metadata_tags(
            metadata_table, metadata_table_ref_column, use_metadata_row_names_as_ref
        )

        # for each id in the table, get the corresponding metadata tags
        tags = [metadata_tags.get(id_, {}) for id_ in table_ids]
        table.set_all_row_tags(tags)
        return table

    @classmethod
    def annotate_columns(
        cls,
        table: Table,
        metadata_table: Table,
        table_ref_row: str = None,
        metadata_table_ref_column: str = None,
        use_table_column_names_as_ref: bool = False,
        use_metadata_row_names_as_ref: bool = False,
    ) -> Table:
        """
        Annotate the columns of a `table` using information from a `metadata_table`.
        All the column values of the reference row of the `table` are matched against the `ids` of the `metadata_table`.
        If an `id` matches against a reference value of the `table`, the corresponding column of the `table` is tagged with the metadata given by the `id`.


        :param table: the table to annotate
        :type table: Table
        :param metadata_table: the metadata table
        :type metadata_table: MetadataTable
        :param table_ref_row: ref row of the table to match against the metadata table
                              If None or empty, the first row is used, defaults to None
        :type table_ref_row: str, optional
        :param metadata_table_ref_column: ref column of the metadata table to match against the table
                                          If None or empty, the first column is used, defaults to None
        :type metadata_table_ref_column: str, optional
        :param use_table_column_as_ref: use the column names of the table as reference, if true the parameter table_ref_row is ignored, defaults to False
        :type use_table_column_as_ref: bool, optional
        :param use_metadata_index_as_ref: use the row names of the metadata table as reference, if true the parameter metadata_table_ref_column is ignored, defaults to False
        :type use_metadata_index_as_ref: bool, optional
        :raises BadRequestException: _description_
        :return: _description_
        :rtype: Table
        """

        # get the list of ids to match against the metadata table
        # from the column name or from the reference row
        table_ids: List[str]

        if use_table_column_names_as_ref:
            # use the index
            table_ids = table.get_column_names()
        elif table_ref_row:
            if not table.row_exists(table_ref_row):
                raise BadRequestException(f"The column '{table_ref_row}' does not exist in table")
            table_ids = table.get_row_data(table_ref_row)
        else:
            # use the first row as reference
            table_ids = table.get_row_data(table.get_row_names()[0])

        # convert each value to string
        table_ids = [str(id_) for id_ in table_ids]
        metadata_tags: Dict[str, Dict[str, str]] = cls._get_metadata_tags(
            metadata_table, metadata_table_ref_column, use_metadata_row_names_as_ref
        )

        # for each id in the table, get the corresponding metadata tags
        tags = [metadata_tags.get(id_, {}) for id_ in table_ids]
        table.set_all_column_tags(tags)
        return table

    @classmethod
    def _get_metadata_tags(
        cls, metadata_table: Table, ref_column: str = None, use_index_as_ref: bool = False
    ) -> Dict[str, Dict[str, str]]:
        """Return the metadata table as dict of tags where key = id and value = tags for the id"""
        dataframe: DataFrame
        if use_index_as_ref:
            # use the index
            dataframe = metadata_table.get_data()

        elif ref_column:
            if not metadata_table.column_exists(ref_column):
                raise BadRequestException(
                    f"The column '{ref_column}' does not exist in metadata table"
                )
            # set the ref column as index name for the dataframe
            dataframe = metadata_table.get_data().set_index(ref_column)
        else:
            # set the first column as the index name for the dataframe
            dataframe = metadata_table.get_data().set_index(metadata_table.get_column_names()[0])

        # dataframe as dict of tags where key = id and value = tags for the id
        dict = dataframe.to_dict("index")

        # force the key to be a string
        return {str(id_): tags for id_, tags in dict.items()}
