

from typing import Callable, Dict

from gws_core.config.param_spec import ParamSpec
from gws_core.core.classes.func_meta_data import FuncArgsMetaData
from gws_core.core.classes.jsonable import DictJsonable
from gws_core.core.utils.utils import Utils

ViewSpecs = Dict[str, ParamSpec]

VIEW_META_DATA_ATTRIBUTE = '__view_mata_data'


class ResourceViewMetaData():
    method_name: str
    human_name: str
    short_description: str
    specs: ViewSpecs
    default_view: bool

    def __init__(self, method_name: str, human_name: str,
                 short_description: str, specs: ViewSpecs,
                 default_view: bool) -> None:
        self.method_name = method_name
        self.human_name = human_name
        self.short_description = short_description
        self.specs = specs
        self.default_view = default_view

    def clone(self) -> 'ResourceViewMetaData':
        return ResourceViewMetaData(self.method_name, self.human_name, self.short_description, self.specs,
                                    self.default_view)

    def to_json(self) -> dict:
        return {
            "method_name": self.method_name,
            "human_name": self.human_name,
            "short_description": self.short_description,
            "specs": DictJsonable(self.specs).to_json(),
            "default_view": self.default_view,
        }


def view(human_name: str = "", short_description: str = "", specs: ViewSpecs = None,
         default_view: bool = False) -> Callable:
    if specs is None:
        specs = {}

    def decorator(func: Callable) -> Callable:
        func_args: FuncArgsMetaData = Utils.get_function_arguments(func)

        if not func_args.is_method():
            raise Exception(
                'The @view decorator must be unsed on a method (with self). It must not be used in a classmethod or a static method')

        # if the view is mark as default, all the parameters must be optional
        if default_view and not func_args.all_args_have_default():
            raise Exception(
                f"View error. The @view of method '{func_args.func_name}' is mark as default but the method has a mandatory argument. If the view is mark as default, all the method's arguments must have a default value")

        # Check that the function arg matches the view specs and the type are the same
        for arg_name in func_args.get_named_args().keys():
            if arg_name not in specs:
                raise Exception(
                    f"View error. The method '{func_args.func_name}' has an argument called '{arg_name}' but this argument is not defined in the specs of the @view decorator")

            # view_param_type: type = specs[arg_name].get_type()
            # if arg_type != view_param_type:
            #     raise Exception(
            #         f"View error. The method '{func.__name__}' has an argument called '{arg_name}' of type '{arg_type}' but this type is not the same as the type defined in the specs of the view decorator '{view_param_type}'")

        # Check that the view specs matches the args types (only is the function does not have an arg or kwargs)
        if not func_args.contain_args():
            for spec_name in specs.keys():
                if spec_name not in func_args.args:
                    raise Exception(
                        f"View error. The @view decorator of the method '{func_args.func_name}' has a spec called '{spec_name}' but there is not argument in the function called with the same name")

        # Create the meta data object
        view_meta_data: ResourceViewMetaData = ResourceViewMetaData(
            func.__name__, human_name, short_description, specs, default_view)
        # Store the meta data object into the view_meta_data_attribute of the function
        setattr(func, VIEW_META_DATA_ATTRIBUTE, view_meta_data)

        return func

    return decorator
