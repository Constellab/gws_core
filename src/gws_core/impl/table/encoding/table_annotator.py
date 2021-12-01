# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from ....config.config_types import ConfigParams, ConfigSpecs
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


@task_decorator(unique_name="TableAnnotator", short_description="Table annotator")
class TableAnnotator(Task):

    input_specs: InputSpecs = {"table": Table, "metadata_table": (MetadataTable, Table)}
    output_specs: OutputSpecs = {"annotated_table": Table}
    config_specs: ConfigSpecs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        metadata_table: MetadataTable = inputs["metadata_table"]
        if isinstance(metadata_table, MetadataTable):
            original_colnames = metadata_table.get_sample_data()
        else:
            # try to use the index (i.e. row_names)
            self.log_warning_message(
                "A Table is used as metadata table. Default indexes will be used for metadata assignment. Please consider using MetadataTable instead of Table.")
            original_colnames = metadata_table.row_names

        annotated_colnames = []
        data: DataFrame = metadata_table.get_data()
        for colname in original_colnames:
            values = data.loc[colname, :].to_list()
            keys = data.columns.to_list()
            row_tab = []
            for i, value in enumerate(values):
                row_tab.append(
                    MetadataTable._format_key_value(keys[i], value)
                )
            annotated_colnames.append(row_tab)

        annotated_colnames = [MetadataTable._TOKEN_SEPARATOR.join(val) for val in annotated_colnames]
        mapper = {name: annotated_colnames[i] for i, name in enumerate(original_colnames)}
        data: DataFrame = inputs["table"].get_data()
        data = data.rename(columns=mapper, inplace=False)
        annotated_table = Table(data=data, row_names=data.index)
        return {"annotated_table": annotated_table}
