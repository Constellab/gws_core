# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.param.param_spec import StrParam
from gws_core.impl.table.helper.dataframe_scaler_helper import \
    DataframeScalerHelper
from gws_core.impl.table.helper.table_scaler_helper import TableScalerHelper

from ....config.config_params import ConfigParams
from ....config.config_types import ConfigSpecs
from ....task.transformer.transformer import Transformer, transformer_decorator
from ..table import Table


@transformer_decorator(
    unique_name="TableScaler",
    resource_type=Table,
    short_description="Scales the numeric values of the table",
)
class TableScaler(Transformer):
    """
    Transformer to apply one scalling function to all numerical values of the table.

    Available scaling functions: ```log2```, ```log10```, ```log```.
    - ```log2, log10``` replace each element by the corresponding log value
    - ```log``` replace each element by the corresponding natural logarithm value
    """
    config_specs: ConfigSpecs = {
        "scaling_function": StrParam(
            human_name="Scaling function",
            allowed_values=DataframeScalerHelper.SCALE_FUNCTIONS,
        )
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        return TableScalerHelper.scale(
            table=source,
            func=params["scaling_function"]
        )


axis_scale_param = StrParam(
    human_name="Scaling function",
    allowed_values=DataframeScalerHelper.AXIS_SCALE_FUNCTIONS,
)


@transformer_decorator(
    unique_name="TableRowScaler",
    resource_type=Table,
    short_description="Scales the numeric values of the table along the row axis",
)
class TableRowScaler(Transformer):
    """
    Transformer to apply one scalling function to all numerical values of the table along the row axis.

    Available scaling functions: ```unit```, ```percent``` and ```standard```.
    - ```unit``` normalizes each element by the sum of its rows
    - ```percent``` is like ```unit``` but the final value is multiplied by 100
    - ```standard``` normalizes each element by the standard deviation of its rows
    """
    config_specs: ConfigSpecs = {
        "scaling_function": axis_scale_param
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        return TableScalerHelper.scale_by_rows(
            table=source,
            func=params["scaling_function"]
        )


@transformer_decorator(
    unique_name="TableColumnScaler",
    resource_type=Table,
    short_description="Scales the numeric values of the table along the column axis",
)
class TableColumnScaler(Transformer):
    """
    Transformer to apply one scalling functions to all numerical values of the table along the column axis.

    Available scaling functions: ```unit```, ```percent``` and ```standard```.
    - ```unit``` normalizes each element by the sum of its columns
    - ```percent``` is like ```unit``` but the final value is multiplied by 100
    - ```standard``` normalizes each element by the standard deviation of its columns
    """

    config_specs: ConfigSpecs = {
        "scaling_function": axis_scale_param
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        return TableScalerHelper.scale_by_columns(
            table=source,
            func=params["scaling_function"]
        )
