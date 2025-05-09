
from typing import Any, List

from numpy import NaN
from pandas import DataFrame

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import BoolParam, StrParam
from gws_core.core.utils.numeric_helper import NumericHelper

from ....task.transformer.transformer import Transformer, transformer_decorator
from ..table import Table


@transformer_decorator(
    unique_name="TableReplace",
    resource_type=Table,
    short_description="Replace values in a table with other values",
)
class TableReplace(Transformer):
    """
    You can provided multiple values to replace. It also supports regex. If multiple values are provided,
    there are replaced sequentially, so the second replace can rewrite the first replace.
    The table's tags are kept.

    For each configuration, if ```Is regex``` is checked, the ```search value``` is considerer as a regex and there is no modification to it.
    Otherwise the ```search value``` is converted (see ```Convertion```). The ```replace value``` is always converted.

    ### Convertion
    The params values supports 2 special values:
    - ```NaN```: convert to NaN
    - ```None```: convert to None

    If the value is someting else, the system tries to convert it to a ```number```. If this is convertible to a ```number``` the system will use the ```number```, otherwise the value is kept as is.


    """

    config_specs = ConfigSpecs({
        "replace_values": ParamSet(ConfigSpecs(
            {"search_value": StrParam(human_name="Value to search for", short_description="Use 'NaN' or 'None' for NaN/None or leave empty for empty string", default_value=""),
             "replace_value": StrParam(human_name="Replace value", short_description="Use 'NaN' for NaN, 'None' for None or leave empty for empty string", default_value=""), "is_regex": BoolParam(
                default_value=False, human_name="Is regex", short_description="If true, the search value is interpreted as a regex"),
             }),
            human_name="Replace values"
        ),
    })

    def transform(self, source: Table, params: ConfigParams) -> Table:
        dataframe: DataFrame = source.get_data()
        replace_values: List[dict] = params.get("replace_values")

        for param in replace_values:
            is_regex: bool = bool(param["is_regex"])

            search_value: Any = None
            if is_regex:
                search_value = param["search_value"]
            else:
                search_value = self.convert_search_value(param["search_value"])

            replace_value: Any = self.convert_replace_value(param["replace_value"])

            dataframe.replace(search_value, replace_value, regex=is_regex, inplace=True)

        new_table = Table(dataframe, row_tags=source.get_row_tags(), column_tags=source.get_column_tags())
        return new_table

    def convert_replace_value(self, param_value: str) -> Any:
        """Handle specific values like NaN and None, and tries to convert to float
      """
        if param_value == 'NaN':
            return NaN
        elif param_value == 'None':
            return None
        else:
            # try to convert to float
            return NumericHelper.to_float(param_value, param_value)

    def convert_search_value(self, param_value: str) -> Any:
        """Handle specific values like NaN and None, and tries to convert to float
      """
        if param_value == 'NaN' or param_value == 'None':
            return NaN
        else:
            # try to convert to float
            return NumericHelper.to_float(param_value, param_value)
