# The component are exported at this level to only load them when they are used
# Because it triggers the loading of the reflex_plugin that load js assets
from .reflex_ag_grid_component.reflex_ag_grid_component import (
    AgGridComponent as AgGridComponent,
)
from .reflex_ag_grid_component.reflex_ag_grid_component import (
    ag_grid_component as ag_grid_component,
)
from .reflex_input_search_component.reflex_input_search_component import (
    InputSearchResultDTO as InputSearchResultDTO,
)
from .reflex_input_search_component.reflex_input_search_component import (
    input_search_component as input_search_component,
)
from .reflex_multi_select_component.reflex_multi_select_component import (
    MultiSelectComponent as MultiSelectComponent,
)
from .reflex_multi_select_component.reflex_multi_select_component import (
    multi_select_component as multi_select_component,
)
from .reflex_rich_text_component.reflex_rich_text_component import (
    RichTextCustomBlocksConfig as RichTextCustomBlocksConfig,
)
from .reflex_rich_text_component.reflex_rich_text_component import (
    RichTextImageConfig as RichTextImageConfig,
)
from .reflex_rich_text_component.reflex_rich_text_component import (
    rich_text_component as rich_text_component,
)
from .reflex_select_component.reflex_select_component import (
    SelectComponent as SelectComponent,
)
from .reflex_select_component.reflex_select_component import (
    select_component as select_component,
)
from .reflex_select_resource_2_component.reflex_select_resource_2_component import (
    SelectResourceInput as SelectResourceInput,
)
from .reflex_select_resource_2_component.reflex_select_resource_2_component import (
    SelectResourceInputDTO as SelectResourceInputDTO,
)
from .reflex_select_resource_2_component.reflex_select_resource_2_component import (
    select_resource_2_component as select_resource_2_component,
)


def _load_plugins():
    """Ensure the gws_plugin is available for the components.

    In the normal flow the plugin was already installed by ReflexProcess (in the server
    process, before the app is built/run), so this is a cheap version check. It only
    self-heals (install from the immutable store) if the app folder copy is missing or
    stale — safe under concurrency, see AppPluginDownloader.
    """
    from ..reflex_plugin import ReflexPlugin  # noqa: PLC0415

    reflex_component = ReflexPlugin()
    reflex_component.install_package()


# Load plugins when this module is imported
_load_plugins()
