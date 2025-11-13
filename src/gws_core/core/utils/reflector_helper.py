
import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from gws_core.core.utils.logger import Logger
from gws_core.core.utils.reflector_types import (ClassicClassDocDTO,
                                                 MethodArgDoc, MethodDoc,
                                                 MethodDocType)

from ..classes.func_meta_data import FuncArgMetaData, FuncArgsMetaData
from ..utils.utils import Utils


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

        parameters: dict[str, inspect.Parameter] = inspect.signature(func).parameters

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

    @classmethod
    def get_method_named_args_json(cls, method: Any) -> List[MethodArgDoc]:
        arguments: Dict[str, FuncArgMetaData] = cls.get_function_arguments(method).get_named_args()
        arguments_json: List[MethodArgDoc] = []
        for arg in arguments.items():
            arg_name: str = arg[0]
            arg_type: Any = arg[1].type_

            arg_default_value: Any = None
            if arg[1].has_default_value():
                arg_default_value = arg[1].default_value if arg[1].default_value is not None else None

            arg_type = Utils.stringify_type(arg_type)
            if arg_type == '_empty':
                if arg_default_value is not None:
                    arg_type = Utils.stringify_type(type(arg_default_value))
                else:
                    arg_type = 'Any'
            if not isinstance(arg_name, str):
                print(arg_name)
            if not isinstance(arg_type, str):
                print(arg_type)
            if isinstance(arg_default_value, str) and len(arg_default_value) == 0:
                arg_default_value = "''"
            if not isinstance(arg_default_value, str):
                if arg_default_value is None:
                    arg_default_value = ''
                else:
                    arg_default_value = str(arg_default_value)

            arguments_json.append(MethodArgDoc(
                arg_name=arg_name,
                arg_type=arg_type,
                arg_default_value=arg_default_value
            ))
        return arguments_json

    @classmethod
    def get_func_doc(cls, func: Callable, type_: Optional[Type] = None) -> Optional[MethodDoc]:
        """Get documentation for a single function.

        :param func: The function to document
        :param type_: Optional type/class to check for method type (classmethod, staticmethod, etc.)
        :return: MethodDoc object or None if documentation cannot be generated
        """
        try:
            if not callable(func):
                return None

            method_type: str = MethodDocType.BASICMETHOD
            func_name = func.__name__

            if type_ is not None:
                if isinstance(inspect.getattr_static(type_, func_name), classmethod):
                    method_type = MethodDocType.CLASSMETHOD

                if isinstance(inspect.getattr_static(type_, func_name), staticmethod):
                    method_type = MethodDocType.STATICMETHOD

            signature: inspect.Signature = inspect.signature(func)
            arguments: List = cls.get_method_named_args_json(func)
            return_type = Utils.stringify_type(
                signature.return_annotation) if signature.return_annotation != inspect.Signature.empty else None

            doc = cls.get_cleaned_doc_string(func)
            return MethodDoc(name=func_name, doc=doc,
                             args=arguments, return_type=return_type, method_type=method_type)
        except Exception:
            Logger.error(f"Error while getting method doc of {func_name}")
            return None

    @classmethod
    def get_all_public_args(cls, type_: Type) -> Optional[Dict[str, str]]:
        """
            Get all the public args of a class and its ancestors
        """
        if not inspect.isclass(type_):
            # return None if the type is not a class
            return None

        res = {}
        for class_ in inspect.getmro(type_):
            res.update(cls.get_public_args(class_))
        return res if len(res) > 0 else None

    @classmethod
    def get_public_args(cls, class_) -> Dict[str, str]:
        '''
            Get the public args of a class
        '''
        arr_variables = [d for (t, d) in inspect.getmembers(class_) if t == '__annotations__']

        if len(arr_variables) == 0:
            return {}

        variables: dict = arr_variables[0]
        try:
            vars_keys = sorted([i for i in variables.keys() if i[0] != '_'])  # get the sorted keys of public variables
            res: Dict = {}
            for k in vars_keys:
                if hasattr(variables[k], '__name__'):
                    res.update({k: variables[k].__name__})
                else:
                    res.update({k: str(variables[k])})
            return res
        except:
            Logger.error(f"Error while getting public args of {class_}")
            return {}

    @classmethod
    def get_public_method_names(cls, type_: Type, include_init: bool = False) -> List[str]:
        """Get the names of all public methods of a class.

        :param type_: The class type to inspect
        :param include_init: Whether to include the __init__ method in the results
        :return: List of public method names
        """
        if not inspect.isclass(type_):
            return []

        methods: Any = inspect.getmembers(
            type_, predicate=inspect.isfunction) + inspect.getmembers(type_, predicate=inspect.ismethod)

        if include_init:
            return [m[0] for m in methods if not m[0].startswith('_') or m[0] == '__init__']
        else:
            return [m[0] for m in methods if not m[0].startswith('_')]

    @classmethod
    def get_public_methods_doc(cls, type_: Type, include_init: bool = False) -> List[MethodDoc]:
        """Get documentation for all public methods of a class.

        :param type_: The class type to inspect
        :param include_init: Whether to include the __init__ method in the results
        :return: List of MethodDoc objects for all public methods
        """
        if not inspect.isclass(type_):
            return []

        # Get public method names
        public_method_names = cls.get_public_method_names(type_, include_init=include_init)

        res: List[MethodDoc] = []
        for public_method in public_method_names:
            method = inspect.getattr_static(type_, public_method)
            method_doc = cls.get_func_doc(method, type_)
            if method_doc is not None:
                res.append(method_doc)
        return res

    @classmethod
    def get_class_docs(cls, type_: Type) -> Optional[ClassicClassDocDTO]:
        """Get the cleaned docstring of a class.

        :param type_: The class type to inspect
        :return: Cleaned docstring of the class or None if not available
        """
        if not inspect.isclass(type_):
            return None

        variables = cls.get_all_public_args(type_)
        methods = cls.get_public_methods_doc(type_, include_init=True)

        name: str = None
        if not hasattr(type_, '__name__'):
            name = str(type_)
        else:
            name = type_.__name__

        doc = cls.get_cleaned_doc_string(type_)
        return ClassicClassDocDTO(name=name, doc=doc, methods=methods, variables=variables)

    @classmethod
    def get_cleaned_doc_string(cls, object_: object) -> str | None:
        """Method to retrieve the doc of a class or a method and clean it
        The clean replace header 1 with header 2

        This is to prevent header 1 in community.
        """
        doc = inspect.getdoc(object_)
        if doc is None:
            return None

        doc = doc.replace('\n# ', '\n## ')

        return doc
