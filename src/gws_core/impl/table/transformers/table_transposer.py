# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ....config.config_params import ConfigParams
from ....config.config_types import ConfigSpecs
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table


@transformer_decorator(unique_name="TableTransposer", resource_type=Table,
                       short_description="Transposes the table",
                       icon="pivot_table_chart")
class TableTransposer(Transformer):
    """
    Transformer to transpose the table (switch columns and lines).

    It also transpose the tags.
    """

    config_specs: ConfigSpecs = {}

    def transform(self, source: Table, params: ConfigParams) -> Table:
        result = source.transpose()
        return result
