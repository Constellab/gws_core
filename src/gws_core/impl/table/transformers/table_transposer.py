from gws_core.model.typing_style import TypingStyle

from ....config.config_params import ConfigParams
from ....config.config_specs import ConfigSpecs
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table


@transformer_decorator(
    unique_name="TableTransposer",
    resource_type=Table,
    short_description="Transposes the table",
    style=TypingStyle.material_icon("pivot_table_chart"),
)
class TableTransposer(Transformer):
    """
    Transformer to transpose the table (switch columns and lines).

    It also transpose the tags.
    """

    config_specs = ConfigSpecs({})

    def transform(self, source: Table, params: ConfigParams) -> Table:
        result = source.transpose()
        return result
