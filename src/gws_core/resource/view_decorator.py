

from typing import Callable, Dict, Type

from ..core.classes.func_meta_data import FuncArgsMetaData
from ..core.classes.jsonable import DictJsonable
from ..core.utils.utils import Utils
from .view import View
from .view_types import ViewSpecs

VIEW_META_DATA_ATTRIBUTE = '__view_mata_data'


class ResourceViewMetaData():
    method_name: str
    view_type: Type[View]
    human_name: str
    short_description: str
    specs: ViewSpecs
    default_view: bool

    def __init__(self, method_name: str, view_type: Type[View],
                 human_name: str, short_description: str,
                 specs: ViewSpecs, default_view: bool) -> None:
        self.method_name = method_name
        self.view_type = view_type
        self.human_name = human_name
        self.short_description = short_description
        self.specs = specs
        self.default_view = default_view

    def clone(self) -> 'ResourceViewMetaData':
        return ResourceViewMetaData(
            self.method_name, self.view_type, self.human_name, self.short_description, self.specs, self.default_view)

    def to_json(self) -> dict:
        return {
            "method_name": self.method_name,
            "view_type": self.view_type._type,
            "human_name": self.human_name,
            "short_description": self.short_description,
            "view_specs": DictJsonable(self.view_type._specs).to_json(),
            "method_specs": DictJsonable(self.specs).to_json(),
            "default_view": self.default_view,
        }


def view(view_type: Type[View], human_name: str = "", short_description: str = "",
         specs: ViewSpecs = None,  default_view: bool = False) -> Callable:
    """ Decorator the place one resource method to define it as a view.
    Views a reference in the interfave when viewing a resource
    It must return a View.

    :param view_type: type of the view returned. If the method can return differents views (not recommended) use View type.
    :type view_type: Type[View]
    :param human_name: Human readable name for the view . Must not be longer than 20 caracters, defaults to ""
    :type human_name: str, optional
    :param short_description: Short description for the view. Must not be longer than 100 caracters, defaults to ""
    :type short_description: str, optional
    :param specs: Specification for the view. The parameters corresponding to the view are passed to the view method when calling it.
     The user can provided values for the specs when calling the view, defaults to None
    :type specs: ViewSpecs, optional
    :param default_view: If true, this view is the one used by default. Chlid class default override the default of parent.
    A default view must contains only optional specs, defaults to False
    :type default_view: bool, optional
    :return: [description]
    :rtype: Callable
    """

    if specs is None:
        specs = {}

    def decorator(func: Callable) -> Callable:
        func_args: FuncArgsMetaData = Utils.get_function_arguments(func)

        if not func_args.is_method():
            raise Exception(
                'The @view decorator must be unsed on a method (with self). It must not be used in a classmethod or a static method')

        # if the view is mark as default, all the parameters must be optional
        if default_view:
            for key, spec in specs.items():
                if not spec.optional:
                    raise Exception(
                        f"View error. The @view of method '{func_args.func_name}' is mark as default but the spec '{key}' is mandatory. If the view is mark as default, all the view specs must be optional or have a default value")

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
            func.__name__, view_type, human_name, short_description, specs, default_view)
        # Store the meta data object into the view_meta_data_attribute of the function
        setattr(func, VIEW_META_DATA_ATTRIBUTE, view_meta_data)

        return func

    return decorator