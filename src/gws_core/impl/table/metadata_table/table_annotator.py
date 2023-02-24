# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.io.io_spec import InputSpec, OutputSpec

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param.param_spec import StrParam
from ....io.io_spec_helper import InputSpecs, OutputSpecs
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ...table.table import Table
from .helper.table_annotator_helper import TableAnnotatorHelper

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

    input_specs: InputSpecs = {
        "sample_table": InputSpec(Table, human_name="Sample table", short_description="Table to annotate"),
        "metadata_table": InputSpec(Table, human_name="Metadata table", short_description="Table containing the metadata")}
    output_specs: OutputSpecs = {"sample_table": OutputSpec(Table)}
    config_specs: ConfigSpecs = {
        "reference_column":
        StrParam(
            default_value="", human_name="Reference column in sample table",
            short_description="Column in the sample table whose values are used for annotation. If empty, is uses the row names."),
        "metadata_ref_column":
        StrParam(
            default_value="", human_name="Reference column in metadata table",
            short_description="Column in the metadata table whose values are used for annotation. If empty, is uses the row names.")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        table: Table = TableAnnotatorHelper.annotate_rows(
            inputs["sample_table"],
            inputs["metadata_table"],
            params.get_value("reference_column"),
            params.get_value("metadata_ref_column"))
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

    input_specs: InputSpecs = {
        "sample_table": InputSpec(Table, human_name="Sample table", short_description="Table to annotate"),
        "metadata_table": InputSpec(Table, human_name="Metadata table", short_description="Table containing the metadata")
    }
    output_specs: OutputSpecs = {"sample_table": OutputSpec(Table)}
    config_specs: ConfigSpecs = {
        "reference_row":
        StrParam(
            default_value="", human_name="Reference row in sample table",
            short_description="Row in the sample table whose data are used as reference for annotation. If empty, it uses the column names."),
        "metadata_ref_column":
        StrParam(
            default_value="", human_name="Reference column in metadata table",
            short_description="Column in the metadata table whose values are used for annotation. If empty, is uses the row names.")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        table: Table = TableAnnotatorHelper.annotate_columns(
            inputs["sample_table"],
            inputs["metadata_table"],
            params.get_value("reference_row"),
            params.get_value("metadata_ref_column"))
        return {"sample_table": table}
