# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from gws_core.config.param_spec import ParamSpec
from gws_core.resource.lazy_view_param import LazyViewParam
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.view_types import ViewSpecs

from ..config.config_types import ConfigParams, ConfigSpecs
from ..config.param_spec_helper import ParamSpecHelper
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.utils.reflector_helper import ReflectorHelper
from ..resource.resource import Resource
from ..resource.view_decorator import VIEW_META_DATA_ATTRIBUTE
from .view import View
from .view_meta_data import ResourceViewMetaData


class ViewHelper():

    @classmethod
    def call_view_on_resource(cls, resource: Resource,
                              view_name: str, config: Dict[str, Any]) -> Dict:

        # Get the view object from the view method
        view: View = cls.call_view_method(resource, view_name, config)

        # check the view config and set default values
        config_params: ConfigParams = ParamSpecHelper.get_config_params(view._specs, config)

        # convert the view to dict using the config
        return view.to_dict(config_params)

    @classmethod
    def call_view_method(cls, resource: Resource,
                         view_name: str, config:  Dict[str, Any]) -> View:

        # check if the view exists
        view_metadata: ResourceViewMetaData = ViewHelper.get_and_check_view(type(resource), view_name)

        # check the method config and set the default values
        if config is None:
            config = {}
        config_params: ConfigParams = ParamSpecHelper.get_config_params(view_metadata.specs, config)

        # Get view method
        view_method: Callable = getattr(resource, view_name)

        # Get the view object from the view method
        view: View = view_method(config_params)

        if view is None or not isinstance(view, View):
            raise Exception(f"The view method '{view_name}' didn't returned a View object")

        return view

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
    def get_views_of_resource_type(cls, resource_type: Type[Resource]) -> List[ResourceViewMetaData]:
        """return all the visible view meta (with method as key name) orderer from the parent class to the child classes

        :param resource_type: [description]
        :type resource_type: Type[Resource]
        :return: [description]
        :rtype: Dict[str, ResourceViewMetaData]
        """

        view_meta_data: Dict[str, ResourceViewMetaData] = {}

        funcs: List[Tuple[str, Callable]] = cls._get_class_view_functions(resource_type)

        for func_tuple in funcs:
            func_name: str = func_tuple[0]
            func: Callable = func_tuple[1]

            # Check if the method is annotated with view
            view_data: ResourceViewMetaData = cls._get_view_function_metadata(func)

            # skip hidden views
            if view_data is None or view_data.hide:
                continue

            # create or override the information
            view_meta_data[func_name] = view_data.clone()

            # force default to false, it is set afterward
            view_meta_data[func_name].default_view = False

        # retrieve the default view and set it
        default_view: ResourceViewMetaData = cls.get_default_view_of_resource_type(resource_type)
        if default_view is not None and not default_view.hide:
            view_meta_data[default_view.method_name] = default_view

        return list(view_meta_data.values())

    @classmethod
    def get_default_view_of_resource_type(cls, resource_type: Type[Resource]) -> Optional[ResourceViewMetaData]:
        """ Method to get the default view of a resource type. It iterates from the parent class to the children and returns
        the last view found

        This method will not work on very werid case when the default view is set on a method, then deactivate by children then reset

        :param resource_type: [description]
        :type resource_type: Type[Resource]
        :return: [description]
        :rtype: Optional[ResourceViewMetaData]
        """

        class_hierarchy: List[Type[Resource]] = cls._get_class_hierarchy(resource_type)
        last_default_name: str = None
        view_meta_data: Dict[str, ResourceViewMetaData] = {}

        for class_ in class_hierarchy:
            funcs: List[Tuple[str, Callable]] = cls._get_class_view_functions(class_)

            for func_tuple in funcs:
                func_name: str = func_tuple[0]
                func: Callable = func_tuple[1]

                # Check if the method is annotated with view
                view_data: ResourceViewMetaData = cls._get_view_function_metadata(func)

                # if the function was already added, refresh the value (it can be overriden by the child class and continue
                if func_name in view_meta_data:
                    view_meta_data[func_name] = view_data
                    continue

                # if the view is a default, consider this one as the default and not the previous one
                if view_data.default_view and not view_data.hide:
                    last_default_name = func_name

                # save the view to skip the function next time we encounter it
                view_meta_data[func_name] = view_data

        return view_meta_data[last_default_name]

    @classmethod
    def get_view_specs(cls, resource_model: ResourceModel, view_name: str) -> ConfigSpecs:
        """Return the config spec for a view of a resource. It converts the ViewSpecs to ConfigSpecs by
        replacing the LazyViewParam to ParamSpec

        :param resource_model: [description]
        :type resource_model: ResourceModel
        :param view_name: [description]
        :type view_name: str
        :raises Exception: [description]
        :return: [description]
        :rtype: ConfigSpecs
        """
        view_meta: ResourceViewMetaData = ViewHelper.get_and_check_view(resource_model.get_resource_type(), view_name)

        view_specs: ViewSpecs = view_meta.merge_specs()
        config_specs: ConfigSpecs = {}

        resource: Resource = None

        for key, value in view_specs.items():
            spec: ParamSpec = None
            if isinstance(value, LazyViewParam):

                # access the resource
                if resource is None:
                    resource = resource_model.get_resource()

                func: Callable = getattr(resource, value.func_name)
                spec = func()

                if not isinstance(spec, ParamSpec):
                    raise Exception('The LazyViewParam did not returned a ParamSpec')
            else:
                spec = value

            # skip the private specs
            if spec.visibility == 'private':
                continue

            # Replace the lazy spec with the ParamSpec generated by the function
            config_specs[key] = spec
        return config_specs

    @classmethod
    def _get_class_view_functions(cls, class_: Callable) -> List[Tuple[str, Callable]]:
        """return all the function that have a view meta data information
        """
        return inspect.getmembers(
            class_, predicate=lambda func: inspect.isfunction(func) and cls._get_view_function_metadata(func) is
            not None)

    @classmethod
    def _get_view_function_metadata(cls, func: Callable) -> ResourceViewMetaData:
        """return the view method metadat if the func is a view, otherwise returns None
        """
        # Check if the method is annotated with view
        return ReflectorHelper.get_and_check_object_metadata(func, VIEW_META_DATA_ATTRIBUTE, ResourceViewMetaData)

    @classmethod
    def _get_class_hierarchy(cls, resource_type: Type[Resource]) -> List[Type[Resource]]:
        parent_types: List[Type[Resource]] = []

        type_ = resource_type
        while(issubclass(type_, Resource)):
            parent_types.insert(0, type_)
            type_ = type_.__base__

        return parent_types
