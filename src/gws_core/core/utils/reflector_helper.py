import inspect
from typing import Any, Callable, Dict, List, Tuple

from ..classes.func_meta_data import FuncArgMetaData, FuncArgsMetaData


class ReflectorHelper():
    """Class to manage reflection and simplify meta data on objects
    """

    @classmethod
    def get_property_names_of_type(cls, class_type: type, type_: type) -> Dict[str, Any]:
        """return the property name and value of all property of a type
        """
        properties: Dict[str, Any] = {}
        member_list: List[Tuple[str, Any]] = inspect.getmembers(class_type)

        for member in member_list:
            member_value = member[1]
            if not inspect.isfunction(member_value) and \
                not inspect.ismethod(member_value) and \
                not inspect.isclass(member_value) and \
                    isinstance(member_value, type_):

                properties[member[0]] = member[1]

        return properties

    @classmethod
    def get_function_arguments(cls, func: Callable) -> FuncArgsMetaData:
        """Function to get the arguments with type (Any if not provided) of a method or a function

        :param func: [description]
        :type func: Callable
        :return: [description]
        :rtype: Dict[str, type]
        """

        parameters: Dict[str, inspect.Parameter] = inspect.signature(func).parameters

        arguments: FuncArgsMetaData = FuncArgsMetaData(func.__name__)

        for arg_name, parameter in parameters.items():
            arguments.add_arg(arg_name, FuncArgMetaData(arg_name=arg_name,
                                                        default_value=parameter._default, type_=parameter._annotation))

        return arguments

    @classmethod
    def function_args_are_optional(cls, func: Callable) -> bool:
        """Function to get the arguments with type (Any if not provided) of a method or a function

        :param func: [description]
        :type func: Callable
        :return: [description]
        :rtype: Dict[str, type]
        """

        func_args: FuncArgsMetaData = cls.get_function_arguments(func)
        return func_args.all_args_have_default()

    @classmethod
    def object_has_metadata(cls, object_: Any, meta_data_name: str, meta_obj_type: type = None) -> bool:
        """Check if the object has meta data. If meta_obj_type is provided, it also check if the type of the metadata is valid
        """
        # Check if the method is annotated with view
        return hasattr(object_, meta_data_name) and (
            meta_obj_type is None or isinstance(getattr(object_, meta_data_name), meta_obj_type))

    @classmethod
    def get_and_check_object_metadata(cls, object_: Any, meta_data_name: str, meta_obj_type: type = None) -> Any:
        """Check and get the object meta data. If meta_obj_type is provided, it also check if the type of the metadata is valid
        """

        if cls.object_has_metadata(object_, meta_data_name, meta_obj_type):
            return getattr(object_, meta_data_name)

        return None

    @classmethod
    def set_object_has_metadata(cls, object_: Any, meta_data_name: str, value: Any) -> bool:
        """Set meta data of an object
        """
        # Check if the method is annotated with view
        return setattr(object_, meta_data_name, value)
