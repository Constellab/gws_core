import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from ..config.param_spec_helper import ParamSpecHelper
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..resource.resource import Resource
from ..resource.view_decorator import VIEW_META_DATA_ATTRIBUTE
from .view import View
from .view_meta_data import ResourceViewMetaData


class ViewHelper():

    @classmethod
    def call_view_on_resource(cls, resource: Resource,
                              view_name: str, method_config: Dict[str, Any], view_config: Dict[str, Any]) -> Dict:

        # Get the view object from the view method
        view: View = cls.call_view_method(resource, view_name, method_config)

        # check the view config and set default values
        view_parameters = ParamSpecHelper.get_and_check_values(view._specs, view_config)

        # convert the view to dict using the config
        return view.to_dict(**view_parameters)

    @classmethod
    def call_view_method(cls, resource: Resource,
                         view_name: str, config:  Dict[str, Any]) -> View:

        # check if the view exists
        view_metadata: ResourceViewMetaData = ViewHelper.get_and_check_view(type(resource), view_name)

        # check the method config and set the default values
        if config is None:
            config = {}
        method_parameters = ParamSpecHelper.get_and_check_values(view_metadata.specs, config)

        # Get view method
        view_method: Callable = getattr(resource, view_name)

        # Get the view object from the view method
        view: View = view_method(**method_parameters)

        if view is None or not isinstance(view, View):
            raise Exception(f"The view method '{view_name}' didn't returned a View object")

        return view

    @classmethod
    def get_default_view_of_resource_type(cls, resource_type: Type[Resource]) -> Optional[ResourceViewMetaData]:

        view_meta_data: List[ResourceViewMetaData] = cls.get_views_of_resource_type(resource_type)

        for view in view_meta_data:
            if view.default_view:
                return view

        return None

    @classmethod
    def get_and_check_view(cls, resource_type: Type[Resource], view_name: str) -> ResourceViewMetaData:
        # check that the method exists and is annotated with view
        if not hasattr(resource_type, view_name):
            raise BadRequestException(f"The resource does not have a view named '{view_name}'")

        view_metadata: ResourceViewMetaData = cls._get_view_function_metadata(getattr(resource_type, view_name))
        if view_metadata is None:
            raise BadRequestException(f"The resource does not have a view named '{view_name}'")
        return view_metadata

    @classmethod
    def _get_view_function_metadata(cls, func: Callable) -> ResourceViewMetaData:
        """return the view method metadat if the func is a view, otherwise returns None
        """
        # Check if the method is annotated with view
        if hasattr(func, VIEW_META_DATA_ATTRIBUTE) and isinstance(
                getattr(func, VIEW_META_DATA_ATTRIBUTE),
                ResourceViewMetaData):

            return getattr(func, VIEW_META_DATA_ATTRIBUTE)

        return None

    @classmethod
    def get_views_of_resource_type(cls, resource_type: Type[Resource]) -> List[ResourceViewMetaData]:
        """return all the view meta (wwith method as key name) orderer from

        :param resource_type: [description]
        :type resource_type: Type[Resource]
        :return: [description]
        :rtype: Dict[str, ResourceViewMetaData]
        """
        class_hierarchy: List[Type[Resource]] = cls._get_class_hierarchy(resource_type)

        resource_type.__base__
        view_meta_data: Dict[str, ResourceViewMetaData] = {}
        last_default: str = None

        for class_ in class_hierarchy:
            funcs: List[Tuple[str, Callable]] = inspect.getmembers(class_, predicate=inspect.isfunction)

            for func_tuple in funcs:
                func_name: str = func_tuple[0]
                func: Callable = func_tuple[1]

                # if the function was already added, continue
                if func_name in view_meta_data:
                    continue

                # Check if the method is annotated with view
                view_data: ResourceViewMetaData = cls._get_view_function_metadata(func)
                if view_data is not None:
                    view_meta_data[func_name] = view_data.clone()

                    # if the view is a default, consider this one as the default and not the previous one
                    if view_data.default_view:
                        if last_default is not None:
                            view_meta_data[last_default].default_view = False
                        last_default = func_name

        return list(view_meta_data.values())

    @classmethod
    def _get_class_hierarchy(cls, resource_type: Type[Resource]) -> List[Type[Resource]]:
        parent_types: List[Type[Resource]] = []

        type_ = resource_type
        while(issubclass(type_, Resource)):
            parent_types.insert(0, type_)
            type_ = type_.__base__

        return parent_types
