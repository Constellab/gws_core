# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ..config.config_params import ConfigParams
from ..config.config_types import ConfigSpecs
from ..impl.table.table import Table
from ..task.transformer.transformer import Transformer, transformer_decorator

# ####################################################################
#
# TableDataFilter class
#
# ####################################################################


@transformer_decorator(
    unique_name="TableDataFilter",
    human_name="Table filter",
    resource_type=Table,
    short_description="Filters the table using various fitering rules",
    deprecated_since="0.3.14",
    deprecated_message="Please use TableRowDataTextFilter, TableColumnDataTextFilter, TableRowDataNumericFilter or TableColumnDataNumericFilter instead",
)
class TableDataFilter(Transformer):
    config_specs: ConfigSpecs = {
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        raise Exception("This task is deprecated. Please use TableDataFilter or TableAggregatorFilter instead")
