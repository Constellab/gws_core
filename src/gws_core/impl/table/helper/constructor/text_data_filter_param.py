# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from .....config.config_types import ConfigParams
from .....config.param_spec import ParamSet, StrParam
from ..table_filter_helper import TableFilterHelper

# ####################################################################
#
# TableFilter class
#
# ####################################################################


class TextDataFilterParamConstructor:

    @staticmethod
    def validate_filter(name: str, data: DataFrame, params: ConfigParams):
        for _filter in params[name]:
            data = TableFilterHelper.filter_text_data(
                data=data,
                column_name=_filter["column_name"],
                comp=_filter["comparator"],
                value=_filter["value"],
            )
        return data

    @staticmethod
    def construct_filter(visibility: str = 'public'):
        return ParamSet(
            {
                "column_name": StrParam(
                    human_name="Column name (pattern)",
                    short_description="The name of the columns along which the filter is applied (regex text pattern); Use '.*' for all the columns",
                    optional=True,
                ),
                "comparator": StrParam(
                    human_name="Comparator",
                    allowed_values=TableFilterHelper.VALID_TEXT_COMPARATORS,
                    short_description="Comparator",
                    optional=True,
                ),
                "value": StrParam(
                    human_name="Searched text (or pattern)",
                    short_description="Searched text. The 'contains' comparator uses regexp text patterns",
                    optional=True,
                ),
            },
            visibility=visibility,
            optional=True,
            human_name="Text data filter",
            short_description="Filter data using a text criterion along a selected set of columns",
            max_number_of_occurrences=9
        )