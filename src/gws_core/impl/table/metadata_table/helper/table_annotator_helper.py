# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from .....config.config_types import ConfigParams, ConfigSpecs
from .....config.param_spec import StrParam
from .....core.exception.exceptions import BadRequestException
from .....io.io_spec_helper import InputSpecs, OutputSpecs
from .....task.task import Task
from .....task.task_decorator import task_decorator
from .....task.task_io import TaskInputs, TaskOutputs
from ....table.table import Table
from ..metadata_table import MetadataTable

# ####################################################################
#
# TableRowAnnotatorHelper class
#
# ####################################################################


class TableRowAnnotatorHelper(Task):
    """
    TableRowAnnotatorHelper

    Annotate the rows of a `sample_table` using information from a `metadata_table`.
    * all the row values of the reference column of the `sample_table` are matched against the `ids` of the `metadata_table`.
    * if an `id` matches against a reference value of the `sample_table`, the corresponding row of the `sample_table` is taggeg with the metadata given by the `id`.
    """

    @classmethod
    def annotate(self, table: Table, metadata_table: MetadataTable, reference_column: str = None) -> Table:
        metadata = metadata_table.get_data().set_index(metadata_table.sample_id_column)
        unsorted_tags: dict = metadata.to_dict('index')

        if reference_column:
            if reference_column not in table.get_data().columns:
                raise BadRequestException(f"No column name '{reference_column}' found in the sample table")
            table_ids: list = table.get_data().loc[:, reference_column].tolist()
            tags = [unsorted_tags.get(id_, {}) for id_ in table_ids]
        else:
            # try to use the index
            table_ids: list = table.get_data().index.tolist()
            tags = [unsorted_tags.get(id_, {}) for id_ in table_ids]
            is_empty = all([t == {} for t in tags])
            if is_empty:
                # try to use the first column instead
                table_ids: list = table.get_data().iloc[:, 0].tolist()
                tags = [unsorted_tags.get(id_, {}) for id_ in table_ids]

        table.set_row_tags(tags)
        return table


# ####################################################################
#
# TableColumnAnnotatorHelper class
#
# ####################################################################

class TableColumnAnnotatorHelper(Task):
    """
    TableColumnAnnotatorHelper

    Annotate the columns of a `sample_table` using information from a `metadata_table`.
    * all the column values of the reference row of the `sample_table` are matched against the `ids` of the `metadata_table`.
    * if an `id` matches against a reference value of the `sample_table`, the corresponding column of the `sample_table` is taggeg with the metadata given by the `id`.
    """

    @classmethod
    def annotate(self, table: Table, metadata_table: MetadataTable, reference_row: str = None) -> Table:
        metadata = metadata_table.get_data().set_index(metadata_table.sample_id_column)
        unsorted_tags: dict = metadata.to_dict('index')

        reference_row = params.get_value("reference_row")
        if reference_row:
            if reference_row not in table.get_data().index:
                raise BadRequestException(f"No row name '{reference_row}' found in the sample table")
            table_ids: list = table.get_data().loc[reference_row, :].tolist()
            tags = [unsorted_tags.get(id_, {}) for id_ in table_ids]
        else:
            # try to use the header
            table_ids: list = table.get_data().columns.tolist()
            tags = [unsorted_tags.get(id_, {}) for id_ in table_ids]
            is_empty = all([t == {} for t in tags])
            if is_empty:
                # try to use the first column instead
                table_ids: list = table.get_data().iloc[0, :].tolist()
                tags = [unsorted_tags.get(id_, {}) for id_ in table_ids]

        table.set_column_tags(tags)
        return {"sample_table": table}
