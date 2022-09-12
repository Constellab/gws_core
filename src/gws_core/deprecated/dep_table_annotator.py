# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.io.io_spec import InputSpec, OutputSpec

from ..config.config_types import ConfigParams, ConfigSpecs
from ..config.param_spec import StrParam
from ..impl.table.metadata_table.metadata_table import MetadataTable
from ..impl.table.table import Table
from ..io.io_spec_helper import InputSpecs, OutputSpecs
from ..task.task import Task
from ..task.task_decorator import task_decorator
from ..task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="TableAnnotator", human_name="Table annotator",
                short_description="Annotate table rows (or columns) according to a metadata table",
                hide=True, deprecated_since='0.2.2',
                deprecated_message='Please use TableRowAnnotator or TableColumnAnnotator instead')
class TableAnnotator(Task):
    """
    TableAnnotator

    Annotate the rows (or columns) of a `sample_table` using information from a `metadata_table`.
    If the rows of the `sample_table` are annotated, then
    * all the row values of the reference column of the `sample_table` are matched against the `ids` of the `metadata_table`.
    * if an `id` matches against a reference value of the `sample_table`, the corresponding row of the `sample_table` is taggeg with the metadata given by the `id`.
    Similarly for `column` annotation.
    """

    input_specs: InputSpecs = {"sample_table": InputSpec(Table), "metadata_table": InputSpec(MetadataTable)}
    output_specs: OutputSpecs = {"annotated_sample_table": OutputSpec(Table)}
    config_specs: ConfigSpecs = {
        "direction":
        StrParam(
            default_value="row", allowed_values=["row", "column"],
            human_name="Direction",
            short_description="Set `row` (`column`) to annotable the rows (or columns) of the sample_table"),
        "reference":
        StrParam(
            default_value="", human_name="Reference",
            short_description="Column (Row) of the sample_table whose values are used as reference values for annotation. It empty, the row (column) names of the sample_table are used."),
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
            table.set_all_row_tags(tags)
        else:
            table_ids: list = table.get_data().columns.tolist()
            tags = [unsorted_tags.get(ids, {}) for ids in table_ids]
            table.set_all_column_tags(tags)
        return {"table": table}
