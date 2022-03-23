# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from ....config.config_types import ConfigParams, ConfigSpecs
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table, TableMeta

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

        def _transpose_meta(meta):
            return {
                "row_tags": meta["column_tags"],
                "column_tags": meta["row_tags"],
                "row_tag_types": meta["column_tag_types"],
                "column_tag_types": meta["row_tag_types"]
            }

        table = Table(
            data=data.T,
            row_names=source.column_names,
            column_names=source.row_names,
            meta=_transpose_meta(source.get_meta())
        )
        return table
