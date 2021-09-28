import inspect
from typing import Callable, Dict, List, Optional, Tuple, Type, Union

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

from ..resource.resource import Resource
from ..resource.view_decorator import (VIEW_META_DATA_ATTRIBUTE,
                                       ResourceViewMetaData)


class ViewHelper():

    @classmethod
    def get_default_view_of_resource_type(cls, resource_type: Type[Resource]) -> Optional[ResourceViewMetaData]:

        view_meta_data: List[ResourceViewMetaData] = cls.get_views_of_resource_type(resource_type)

        for view in view_meta_data:
            if view.default_view:
                return view

        return None

    @classmethod
    def check_view(cls, resource_type: Type[Resource], view_name: str) -> None:
        # check that the method exists and is annotated with view
        if (not hasattr(resource_type, view_name)) or cls._get_view_metadata(getattr(resource_type, view_name)) is None:
            raise BadRequestException(f"The resource does not have a view named '{view_name}'")

    @classmethod
    def _get_view_metadata(cls, func: Callable) -> ResourceViewMetaData:
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
                view_data: ResourceViewMetaData = cls._get_view_metadata(func)
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
