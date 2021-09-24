

from typing import Callable, Dict

from gws_core.config.param_spec import ParamSpec

ViewSpecs = Dict[str, ParamSpec]

VIEW_META_DATA_ATTRIBUTE = '__view_mata_data'


class ResourceViewMetaData():
    method_name: str
    human_name: str
    short_description: str
    specs: ViewSpecs

    def __init__(self, method_name: str, human_name: str,
                 short_description: str, specs: ViewSpecs) -> None:
        self.method_name = method_name
        self.human_name = human_name
        self.short_description = short_description
        self.specs = specs


def view(human_name: str = "", short_description: str = "", specs: ViewSpecs = None) -> Callable:

    def decorator(func: Callable) -> Callable:
        # Create the meta data object
        view_meta_data: ResourceViewMetaData = ResourceViewMetaData(func.__name__, human_name, short_description, specs)
        # Store the meta data object into the view_meta_data_attribute of the function
        setattr(func, VIEW_META_DATA_ATTRIBUTE, view_meta_data)

        return func

    return decorator
