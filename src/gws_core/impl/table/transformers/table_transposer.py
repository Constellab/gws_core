# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from gws_core.resource.technical_info import TechnicalInfo

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
    """
    Transformer to transpose the table (switch columns and lines).

    It also transpose the tags.
    """

    config_specs: ConfigSpecs = {}

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        result = source.transpose()
        return result
