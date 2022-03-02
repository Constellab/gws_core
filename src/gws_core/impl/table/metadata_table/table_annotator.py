# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import StrParam
from ....core.exception.exceptions import BadRequestException
from ....io.io_spec import InputSpecs, OutputSpecs
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ...table.table import Table
from .metadata_table import MetadataTable

# ####################################################################
#
# TableRowAnnotator class
#
# ####################################################################


@task_decorator(unique_name="TableRowAnnotator", human_name="Table row annotator",
                short_description="Annotate table rows according to a metadata table")
class TableRowAnnotator(Task):
    """
    TableRowAnnotator

    Annotate the rows of a `sample_table` using information from a `metadata_table`.
    * all the row values of the reference column of the `sample_table` are matched against the `ids` of the `metadata_table`.
    * if an `id` matches against a reference value of the `sample_table`, the corresponding row of the `sample_table` is taggeg with the metadata given by the `id`.
    """

    input_specs: InputSpecs = {"sample_table": Table, "metadata_table": MetadataTable}
    output_specs: OutputSpecs = {"sample_table": Table}
    config_specs: ConfigSpecs = {
        "reference_column":
        StrParam(
            default_value="", human_name="Reference column",
            short_description="Column whose data are used as reference for annotation. It empty, the row names are used.")
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        table: Table = inputs["sample_table"]
        metadata_table: MetadataTable = inputs["metadata_table"]
        metadata = metadata_table.get_data()
        metadata.set_index(metadata_table.sample_id_column, inplace=True)
        unsorted_tags: dict = metadata.to_dict('index')

        reference_column = params.get_value("reference_column")
        if reference_column:
            if reference_column not in table.get_data().columns:
                raise BadRequestException(f"No column name '{reference_column}' found in the sample table")
            table_ids: list = table.get_data().loc[:, reference_column].tolist()
        else:
            table_ids: list = table.get_data().index.tolist()
        tags = [unsorted_tags.get(ids, {}) for ids in table_ids]
        table.set_row_tags(tags)
        return {"sample_table": table}


# ####################################################################
#
# TableColumnAnnotator class
#
# ####################################################################

@task_decorator(unique_name="TableColumnAnnotator", human_name="Table column annotator",
                short_description="Annotate table columns according to a metadata table")
class TableColumnAnnotator(Task):
    """
    TableColumnAnnotator

    Annotate the columns of a `sample_table` using information from a `metadata_table`.
    * all the column values of the reference row of the `sample_table` are matched against the `ids` of the `metadata_table`.
    * if an `id` matches against a reference value of the `sample_table`, the corresponding column of the `sample_table` is taggeg with the metadata given by the `id`.
    """

    input_specs: InputSpecs = {"sample_table": Table, "metadata_table": MetadataTable}
    output_specs: OutputSpecs = {"sample_table": Table}
    config_specs: ConfigSpecs = {
        "reference_row":
        StrParam(
            default_value="", human_name="Reference row",
            short_description="Row whose data are used as reference for annotation. It empty, the headers are used.")
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        table: Table = inputs["sample_table"]
        metadata_table: MetadataTable = inputs["metadata_table"]
        metadata = metadata_table.get_data()
        metadata.set_index(metadata_table.sample_id_column, inplace=True)
        unsorted_tags: dict = metadata.to_dict('index')

        reference_row = params.get_value("reference_row")
        if reference_row:
            if reference_row not in table.get_data().index:
                raise BadRequestException(f"No row name '{reference_row}' found in the sample table")
            table_ids: list = table.get_data().loc[reference_row, :].tolist()
        else:
            table_ids: list = table.get_data().columns.tolist()
        tags = [unsorted_tags.get(ids, {}) for ids in table_ids]
        table.set_column_tags(tags)
        return {"sample_table": table}
