# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import StrParam
from ....io.io_spec import InputSpecs, OutputSpecs
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ...table.table import Table
from .metadata_table import MetadataTable

# ####################################################################
#
# TableAnnotator class
#
# ####################################################################


@task_decorator(unique_name="TableAnnotator", human_name="Table annotator",
                short_description="Annotator column (or row) name according to a metadata table")
class TableAnnotator(Task):

    input_specs: InputSpecs = {"table": Table, "metadata_table": MetadataTable}
    output_specs: OutputSpecs = {"table": Table}
    config_specs: ConfigSpecs = {
        "axis": StrParam(default_value="row", allowed_values=["row", "column"],
                         human_name="Axis", short_description="Set axis='row' (or 'column'), to use row (or column) names to annotated to table")
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        table: Table = inputs["table"]
        metadata_table: MetadataTable = inputs["metadata_table"]
        metadata = metadata_table.get_data()
        metadata.set_index(metadata_table.sample_id_column, inplace=True)
        unsorted_tags: dict = metadata.to_dict('index')

        if params["axis"] == "row":
            table_ids: list = table.get_data().index.tolist()
            tags = [unsorted_tags.get(ids, {}) for ids in table_ids]
            table.set_row_tags(tags)
        else:
            table_ids: list = table.get_data().columns.tolist()
            tags = [unsorted_tags.get(ids, {}) for ids in table_ids]
            table.set_column_tags(tags)

        table.name = table.name + " (Annotated)"
        return {"table": table}
