# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

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
    - ```log2, log10``` replace each element by the corresponding log value
    - ```unit``` normalizes each element by the sum of its column
    - ```percent``` is like ```unit``` but the final value is multiplied by 100.
    - ```percent``` normalizes each element by the standard deviation of its column
    """
    config_specs: ConfigSpecs = {
        "scaling": DataScaleFilterParamConstructor.construct_filter(),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        data: DataFrame = DataScaleFilterParamConstructor.scale(source.get_data(), params["scaling"])
        table = source.create_sub_table(data, source.get_meta())
        return table
