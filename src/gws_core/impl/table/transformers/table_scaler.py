# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ....config.config_types import ConfigParams, ConfigSpecs
from ....task.transformer.transformer import Transformer, transformer_decorator
from ..helper.constructor.data_scale_filter_param import \
    DataScaleFilterParamConstructor
from ..table import Table

# ####################################################################
#
# TableScaler class
#
# ####################################################################


@transformer_decorator(
    unique_name="TableScaler",
    resource_type=Table,
    short_description="Scales the numeric values of the table",
)
class TableScaler(Transformer):
    """
    Transformer to apply one or multiple scalling functions to all numerical values of the table.

    Available scaling functions: ```log2```, ```log10```, ```unit```, ```percent``` and ```standard```.
    """
    config_specs: ConfigSpecs = {
        "scaling": DataScaleFilterParamConstructor.construct_filter(),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        data = source.get_data()
        data: Table = DataScaleFilterParamConstructor.scale(data, params["scaling"])
        table = Table(data=data)
        # table.name = source.name + " (Scaled)"
        return table
