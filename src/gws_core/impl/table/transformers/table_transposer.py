

from gws_core.config.param.param_spec import StrParam
from gws_core.model.typing_style import TypingStyle

from ....config.config_params import ConfigParams
from ....config.config_types import ConfigSpecs
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table

allowed_values = []
for i in range(1, 100):
    allowed_values.append('Column ' + str(i))


@transformer_decorator(unique_name="TableTransposer", resource_type=Table,
                       short_description="Transposes the table",
                       style=TypingStyle.material_icon("pivot_table_chart"))
class TableTransposer(Transformer):
    """
    Transformer to transpose the table (switch columns and lines).

    It also transpose the tags.
    """

    config_specs: ConfigSpecs = {'test': StrParam(allowed_values=allowed_values)}

    def transform(self, source: Table, params: ConfigParams) -> Table:
        result = source.transpose()
        return result
