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
    config_specs: ConfigSpecs = {
        "scaling": DataScaleFilterParamConstructor.construct_filter(),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        data = source.get_data()
        data = DataScaleFilterParamConstructor.validate_filter("scaling", data, params)
        return Table(data=data)
