# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from ....config.config_types import ConfigParams, ConfigSpecs
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table

# ####################################################################
#
# TableTransposer class
#
# ####################################################################


@transformer_decorator(unique_name="TableTransposer", resource_type=Table, short_description="Transposes the table")
class TableTransposer(Transformer):

    config_specs: ConfigSpecs = {}

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        data: DataFrame = source.get_data()
        table = Table(
            data=data.T,
            row_names=source.column_names,
            column_names=source.row_names
        )
        table.name = source.name + " (Transposed)"
        return table
