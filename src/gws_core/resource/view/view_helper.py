import inspect
from typing import Callable, Dict, List, Tuple, Type

from gws_core.core.utils.utils import Utils

from ...core.exception.exceptions.bad_request_exception import BadRequestException
from ...core.utils.reflector_helper import ReflectorHelper
from ..resource import Resource
from .view_decorator import VIEW_META_DATA_ATTRIBUTE
from .view_meta_data import ResourceViewMetaData


class ViewHelper:
    DEFAULT_VIEW_NAME = "default-view"

    @classmethod
    def get_and_check_view_meta(
        cls, resource_type: Type[Resource], view_name: str
    ) -> ResourceViewMetaData:
        if not Utils.issubclass(resource_type, Resource):
            raise BadRequestException("The provided type is not a Resource type")

        # specific case for the default view, we retrieve the view name
        if view_name == cls.DEFAULT_VIEW_NAME:
            return ViewHelper.get_default_view_of_resource_type(resource_type)

        # check that the method exists and is annotated with view
        if not hasattr(resource_type, view_name):
            raise BadRequestException(f"The resource does not have a view named '{view_name}'")

        view_metadata: ResourceViewMetaData = cls._get_view_function_metadata(
            getattr(resource_type, view_name)
        )
        if view_metadata is None:
            raise BadRequestException(f"The resource does not have a view named '{view_name}'")
        return view_metadata

    @classmethod
    def get_views_of_resource_type(
        cls, resource_type: Type[Resource]
    ) -> List[ResourceViewMetaData]:
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
    def get_default_view_of_resource_type(
        cls, resource_type: Type[Resource]
    ) -> ResourceViewMetaData:
        """Method to get the default view of a resource type. It iterates from the parent class to the children and returns
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
    def _get_class_view_functions(cls, class_: Callable) -> List[Tuple[str, Callable]]:
        """return all the function that have a view meta data information"""
        return inspect.getmembers(
            class_,
            predicate=lambda func: inspect.isfunction(func)
            and cls._get_view_function_metadata(func) is not None,
        )

    @classmethod
    def _get_view_function_metadata(cls, func: Callable) -> ResourceViewMetaData:
        """return the view method metadat if the func is a view, otherwise returns None"""
        # Check if the method is annotated with view
        view_meta: ResourceViewMetaData = ReflectorHelper.get_and_check_object_metadata(
            func, VIEW_META_DATA_ATTRIBUTE, ResourceViewMetaData
        )

        if view_meta:
            return view_meta.clone()

        return None

    @classmethod
    def _get_class_hierarchy(cls, resource_type: Type[Resource]) -> List[Type[Resource]]:
        parent_types: List[Type[Resource]] = []

        type_ = resource_type
        while issubclass(type_, Resource):
            parent_types.insert(0, type_)
            type_ = type_.__base__

        return parent_types
