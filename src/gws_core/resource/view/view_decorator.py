

from typing import Callable, Type

from gws_core.brick.brick_service import BrickService
from gws_core.core.utils.utils import Utils
from gws_core.model.typing_style import TypingStyle

from ...config.param.param_spec import ParamSpec
from ...core.classes.func_meta_data import FuncArgsMetaData
from ...core.utils.reflector_helper import ReflectorHelper
from .view import View
from .view_meta_data import ResourceViewMetaData
from .view_types import ViewSpecs

VIEW_META_DATA_ATTRIBUTE = '_view_mata_data'


def view(view_type: Type[View],
         human_name: str = "",
         short_description: str = "",
         specs: ViewSpecs = None,
         default_view: bool = False,
         hide: bool = False,
         style: TypingStyle = None) -> Callable:
    """ Decorator the place one resource method to define it as a view.
    Views a reference in the interfave when viewing a resource
    It must return a View.

    :param view_type: type of the view returned. If the method can return differents views (not recommended) use View type.
    :type view_type: Type[View]
    :param human_name: Human readable name for the view., defaults to ""
    :type human_name: str, optional
    :param short_description: Short description for the view. Must not be longer than 255 caracters., defaults to ""
    :type short_description: str, optional
    :param specs: Specification for the view. The parameters corresponding to the view are passed to the view method when calling it.
     The user can provided values for the specs when calling the view, defaults to None
    :type specs: ViewSpecs, optional
    :param default_view: If true, this view is the one used by default. Chlid class default override the default of parent.
    A default view must contains only optional specs, defaults to False
    :type default_view: bool, optional
    :param hide: If true the view will not be listed in the interface.
                It is useful when you overrided a class and you don't wan't to activate this view anymore, defaults to False
    :type hide: bool, optional
    :param style: style of the task, view TypingStyle object for more info.
                    This overrides the default style define by the view type, defaults to None
    :type style: TypingStyle, optional
    :return: [description]
    :rtype: Callable
    """

    if specs is None:
        specs = {}

    # provide the style default value
    if style:
        style.fill_empty_values()

    def decorator(func: Callable) -> Callable:

        try:

            func_args: FuncArgsMetaData = ReflectorHelper.get_function_arguments(func)

            if not func_args.is_method():
                raise Exception(
                    'The @view decorator must be unsed on a method (with self). It must not be used in a classmethod or a static method')

            if not Utils.issubclass(view_type, View):
                raise Exception(
                    f"View error. The view type '{view_type}' of the @view of method '{func_args.func_name}' is not a sub type of View")

            # if the view is mark as default, all the parameters must be optional
            if default_view:
                if hide:
                    raise Exception(
                        f"View error. The @view of method '{func_args.func_name}' is mark as default and hide. The default view can't be hidden")

                for spec_name, spec in specs.items():
                    if not spec.optional:
                        raise Exception(
                            f"View error. The @view of method '{func_args.func_name}' is mark as default but the spec '{spec_name}' is mandatory. If the view is mark as default, all the view specs must be optional or have a default value")

            # # Check that the function arg matches the view specs and the type are the same
            # for arg_name in func_args.get_named_args().keys():
            #     if arg_name not in specs:
            #         raise Exception(
            #             f"View error. The method '{func_args.func_name}' has an argument called '{arg_name}' but this argument is not defined in the specs of the @view decorator")

                # view_param_type: type = specs[arg_name].get_type()
                # if arg_type != view_param_type:
                #     raise Exception(
                #         f"View error. The method '{func.__name__}' has an argument called '{arg_name}' of type '{arg_type}' but this type is not the same as the type defined in the specs of the view decorator '{view_param_type}'")

            # # Check that the view specs matches the args types (only is the function does not have an arg or kwargs)
            # if not func_args.contain_args():
            #     for spec_name in specs.keys():
            #         if spec_name not in func_args.args:
            #             raise Exception(
            #                 f"View error. The @view decorator of the method '{func_args.func_name}' has a spec called '{spec_name}' but there is not argument in the function called with the same name")

            # Check the specs
            if not isinstance(specs, dict):
                raise Exception("The view specs must be a dictionary")

            for key, item in specs.items():
                if not isinstance(item, ParamSpec):
                    raise Exception(
                        f"The config spec '{key}' is invalid, it must be a ParamSpec or a LazyViewParam but got {type(item)}")

            # If method spec overides view spec, check the type
            view_specs: ViewSpecs = view_type._specs
            if len(specs) > 0 and len(view_specs) > 0:
                for spec_name, method_spec in specs.items():
                    # if the method spec overide the view spec
                    if spec_name in view_specs:
                        view_spec: ParamSpec = view_specs[spec_name]
                        # the method spec must be a sub class of the view spec
                        if not isinstance(method_spec, type(view_spec)):
                            raise Exception(
                                f"View error. The @view decorator of the method '{func_args.func_name}' has a spec called '{spec_name}' that overide the spec of the view '{view_type}' but the types are imcompatible")

            # Create the meta data object
            view_meta_data: ResourceViewMetaData = ResourceViewMetaData(
                func.__name__, view_type, human_name, short_description,
                specs, default_view, hide, style)
            # Store the meta data object into the view_meta_data_attribute of the function
            ReflectorHelper.set_object_has_metadata(func, VIEW_META_DATA_ATTRIBUTE, view_meta_data)
        except Exception as e:
            BrickService.log_brick_error(func, str(e))
        return func

    return decorator
