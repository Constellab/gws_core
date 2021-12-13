# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from .....config.config_types import ConfigParams
from .....config.param_spec import ParamSet, StrParam
from .....core.exception.exceptions import BadRequestException
from ..table_scaler_helper import TableScalerHelper

# ####################################################################
#
# TableFilter class
#
# ####################################################################


class DataScaleFilterParamConstructor:

    @staticmethod
    def validate_filter(name: str, data: DataFrame, params: ConfigParams):
        for _filter in params[name]:
            data = TableScalerHelper.scale(
                data=data,
                func=_filter["scaling_function"]
            )
        return data

    @staticmethod
    def construct_filter(visibility: str = 'public', allowed_values=None):
        if allowed_values is not None:
            for val in allowed_values:
                if val not in TableScalerHelper.VALID_SCALING_FUNCTIONS:
                    raise BadRequestException(
                        f"Value {val} cannot be an allowed value. Valid values are {TableScalerHelper.VALID_SCALING_FUNCTIONS}")
        else:
            allowed_values = TableScalerHelper.VALID_SCALING_FUNCTIONS

        return ParamSet(
            {
                "scaling_function": StrParam(
                    human_name="Scaling function",
                    allowed_values=allowed_values,
                    short_description="Scaling function",
                    optional=True,
                ),
            },
            visibility=visibility,
            optional=True,
            human_name="Data scaler",
            short_description="Scale data using a numeric function",
            max_number_of_occurrences=9
        )
