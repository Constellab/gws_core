# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.io.io_spec import InputSpec, OutputSpec

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param.param_spec import BoolParam, StrParam
from ....io.io_specs import InputSpecs, OutputSpecs
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

    input_specs: InputSpecs = InputSpecs({
        "sample_table": InputSpec(Table, human_name="Sample table", short_description="Table to annotate"),
        "metadata_table": InputSpec(Table, human_name="Metadata table", short_description="Table containing the metadata")})
    output_specs: OutputSpecs = OutputSpecs({"sample_table": OutputSpec(Table)})
    config_specs: ConfigSpecs = {
        "reference_column":
        StrParam(
            default_value="", human_name="Reference column in sample table",
            short_description="Column in the sample table whose values are used for annotation. If empty, it uses the first column."),
        "metadata_ref_column":
        StrParam(
            default_value="", human_name="Reference column in metadata table",
            short_description="Column in the metadata table whose values are used for annotation. If empty, it uses the first column."),
        "use_table_row_names_as_ref":  BoolParam(
            default_value=False, human_name="Use sample table row names as reference", visibility="protected",
            short_description="If checked, the row names of the sample table are used as reference for annotation and the reference column param is ignored."),
        "use_metadata_row_names_as_ref":  BoolParam(
            default_value=False, human_name="Use metadata table row names as reference", visibility="protected",
            short_description="If checked, the row names of the metadata table are used as reference for annotation and the metadata reference column param is ignored.")
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        reference_column = params.get_value("reference_column")
        metadata_ref_column = params.get_value("metadata_ref_column")
        use_table_row_names_as_ref = params.get_value("use_table_row_names_as_ref")
        use_metadata_row_names_as_ref = params.get_value("use_metadata_row_names_as_ref")

        if use_table_row_names_as_ref:
            self.log_info_message("Using sample table row names as reference for annotation")
        elif reference_column:
            self.log_info_message(f"Using sample table column '{reference_column}' as reference for annotation")
        else:
            self.log_info_message("Using sample table first column as reference for annotation")

        if use_metadata_row_names_as_ref:
            self.log_info_message("Using metadata table row names as reference for annotation")
        elif metadata_ref_column:
            self.log_info_message(f"Using metadata table column '{metadata_ref_column}' as reference for annotation")
        else:
            self.log_info_message("Using metadata table first column as reference for annotation")

        table: Table = TableAnnotatorHelper.annotate_rows(
            inputs["sample_table"],
            inputs["metadata_table"],
            reference_column,
            metadata_ref_column,
            use_table_row_names_as_ref,
            use_metadata_row_names_as_ref)
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

    input_specs: InputSpecs = InputSpecs({
        "sample_table": InputSpec(Table, human_name="Sample table", short_description="Table to annotate"),
        "metadata_table": InputSpec(Table, human_name="Metadata table", short_description="Table containing the metadata")
    })
    output_specs: OutputSpecs = OutputSpecs({"sample_table": OutputSpec(Table)})
    config_specs: ConfigSpecs = {
        "reference_row":
        StrParam(
            default_value="", human_name="Reference row in sample table",
            short_description="Row in the sample table whose data are used as reference for annotation. If empty, it uses the first row."),
        "metadata_ref_column":
        StrParam(
            default_value="", human_name="Reference column in metadata table",
            short_description="Column in the metadata table whose values are used for annotation. If empty, it uses the first column."),
        "use_table_column_names_as_ref":  BoolParam(
            default_value=False, human_name="Use sample table column names as reference", visibility="protected",
            short_description="If checked, the column names of the sample table are used as reference for annotation and the reference row param is ignored."),
        "use_metadata_row_names_as_ref":  BoolParam(
            default_value=False, human_name="Use metadata table row names as reference", visibility="protected",
            short_description="If checked, the row names of the metadata table are used as reference for annotation and the metadata reference column param is ignored.")
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        reference_row = params.get_value("reference_row")
        metadata_ref_column = params.get_value("metadata_ref_column")
        use_table_column_names_as_ref = params.get_value("use_table_column_names_as_ref")
        use_metadata_row_names_as_ref = params.get_value("use_metadata_row_names_as_ref")

        if use_table_column_names_as_ref:
            self.log_info_message("Using sample table column names as reference for annotation")
        elif reference_row:
            self.log_info_message(f"Using sample table row '{reference_row}' as reference for annotation")
        else:
            self.log_info_message("Using sample table first row as reference for annotation")

        if use_metadata_row_names_as_ref:
            self.log_info_message("Using metadata table row names as reference for annotation")
        elif metadata_ref_column:
            self.log_info_message(f"Using metadata table column '{metadata_ref_column}' as reference for annotation")
        else:
            self.log_info_message("Using metadata table first column as reference for annotation")

        table: Table = TableAnnotatorHelper.annotate_columns(
            inputs["sample_table"],
            inputs["metadata_table"],
            reference_row,
            metadata_ref_column,
            use_table_column_names_as_ref,
            use_metadata_row_names_as_ref)
        return {"sample_table": table}
