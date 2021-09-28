

from typing import Callable, Dict

from gws_core.config.param_spec import ParamSpec
from gws_core.core.utils.utils import Utils

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
    if specs is None:
        specs = {}

    def decorator(func: Callable) -> Callable:
        func_args: Dict[str, type] = Utils.get_function_arguments(func)

        if 'self' not in func_args:
            raise Exception(
                'The @view decorator must be unsed on a method (with self). It must not be used in a classmethod or a static method')

        # Check that the function arg matches the view specs and the type are the same
        for arg_name in func_args.keys():
            if arg_name == 'self':
                continue

            if arg_name not in specs:
                raise Exception(
                    f"View error. The method '{func.__name__}' has an argument called '{arg_name}' but this argument is not defined in the specs of the @view decorator")

            # view_param_type: type = specs[arg_name].get_type()
            # if arg_type != view_param_type:
            #     raise Exception(
            #         f"View error. The method '{func.__name__}' has an argument called '{arg_name}' of type '{arg_type}' but this type is not the same as the type defined in the specs of the view decorator '{view_param_type}'")

        # Check that the view specs mathces the args types
        for spec_name, param_spec in specs.items():
            if spec_name not in func_args:
                raise Exception(
                    f"View error. The @view decorator of the method '{func.__name__}' has a spec called '{arg_name}' but there is not argument in the function called with the same name")

        # Create the meta data object
        view_meta_data: ResourceViewMetaData = ResourceViewMetaData(func.__name__, human_name, short_description, specs)
        # Store the meta data object into the view_meta_data_attribute of the function
        setattr(func, VIEW_META_DATA_ATTRIBUTE, view_meta_data)

        return func

    return decorator
