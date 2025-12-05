import inspect
from collections.abc import Callable
from typing import Any, cast

from gws_core.core.utils.logger import Logger
from gws_core.core.utils.reflector_types import (
    ClassicClassDocDTO,
    MethodArgDoc,
    MethodDoc,
    MethodDocType,
)

from ..classes.func_meta_data import FuncArgMetaData, FuncArgsMetaData
from ..utils.utils import Utils


class ReflectorHelper:
    """Class to manage reflection and simplify meta data on objects"""

    @classmethod
    def get_property_names_of_type(cls, class_type: type, type_: type) -> dict[str, Any]:
        """Get all properties of a class that match a specific type.

        Retrieves non-callable, non-class members of a class that are instances
        of the specified type.

        :param class_type: The class to inspect for properties
        :type class_type: type
        :param type_: The type to filter properties by
        :type type_: type
        :return: Dictionary mapping property names to their values
        :rtype: Dict[str, Any]

        Example:
            >>> class MyClass:
            ...     text: str = "hello"
            ...     number: int = 42
            >>> ReflectorHelper.get_property_names_of_type(MyClass, str)
            {'text': 'hello'}
        """
        properties: dict[str, Any] = {}
        member_list: list[tuple[str, Any]] = inspect.getmembers(class_type)

        for member in member_list:
            member_value = member[1]
            if (
                not inspect.isfunction(member_value)
                and not inspect.ismethod(member_value)
                and not inspect.isclass(member_value)
                and isinstance(member_value, type_)
            ):
                properties[member[0]] = member[1]

        return properties

    @classmethod
    def get_function_arguments(cls, func: Callable[..., Any]) -> FuncArgsMetaData:
        """Extract metadata about all arguments of a function or method.

        Analyzes a function's signature and returns detailed metadata about each
        argument including its name, type annotation, and default value.

        :param func: The function or method to analyze
        :type func: Callable[..., Any]
        :return: Metadata object containing information about all function arguments
        :rtype: FuncArgsMetaData

        Note:
            - Type annotations default to 'Any' if not specified
            - Captures default values for optional parameters
            - Works with both functions and methods
        """

        parameters: dict[str, inspect.Parameter] = inspect.signature(func).parameters

        arguments: FuncArgsMetaData = FuncArgsMetaData(func.__name__)

        for arg_name, parameter in parameters.items():
            arguments.add_arg(
                arg_name,
                FuncArgMetaData(
                    arg_name=arg_name, default_value=parameter._default, type_=parameter._annotation
                ),
            )

        return arguments

    @classmethod
    def function_args_are_optional(cls, func: Callable[..., Any]) -> bool:
        """Check if all arguments of a function have default values.

        Determines whether a function can be called without providing any arguments,
        i.e., all parameters have default values.

        :param func: The function or method to check
        :type func: Callable[..., Any]
        :return: True if all arguments have default values, False otherwise
        :rtype: bool

        Example:
            >>> def func1(a, b=1): pass
            >>> def func2(a=1, b=2): pass
            >>> ReflectorHelper.function_args_are_optional(func1)
            False
            >>> ReflectorHelper.function_args_are_optional(func2)
            True
        """

        func_args: FuncArgsMetaData = cls.get_function_arguments(func)
        return func_args.all_args_have_default()

    @classmethod
    def object_has_metadata(
        cls, object_: Any, meta_data_name: str, meta_obj_type: type = None
    ) -> bool:
        """Check if an object has a specific metadata attribute.

        Verifies whether an object has an attribute with the given name, and optionally
        validates that the attribute is of a specific type.

        :param object_: The object to check for metadata
        :type object_: Any
        :param meta_data_name: The name of the metadata attribute to look for
        :type meta_data_name: str
        :param meta_obj_type: Optional type to validate the metadata against
        :type meta_obj_type: type
        :return: True if the metadata exists (and matches the type if specified), False otherwise
        :rtype: bool

        Example:
            >>> class MyClass:
            ...     my_meta = "value"
            >>> obj = MyClass()
            >>> ReflectorHelper.object_has_metadata(obj, "my_meta")
            True
            >>> ReflectorHelper.object_has_metadata(obj, "my_meta", str)
            True
            >>> ReflectorHelper.object_has_metadata(obj, "my_meta", int)
            False
        """
        # Check if the method is annotated with view
        return hasattr(object_, meta_data_name) and (
            meta_obj_type is None or isinstance(getattr(object_, meta_data_name), meta_obj_type)
        )

    @classmethod
    def get_and_check_object_metadata(
        cls, object_: Any, meta_data_name: str, meta_obj_type: type = None
    ) -> Any:
        """Retrieve metadata from an object with optional type validation.

        Gets the value of a metadata attribute if it exists on the object, with optional
        type checking. Returns None if the metadata doesn't exist or fails type validation.

        :param object_: The object to retrieve metadata from
        :type object_: Any
        :param meta_data_name: The name of the metadata attribute to retrieve
        :type meta_data_name: str
        :param meta_obj_type: Optional type to validate the metadata against
        :type meta_obj_type: type
        :return: The metadata value if it exists and passes validation, None otherwise
        :rtype: Any

        Example:
            >>> class MyClass:
            ...     my_meta = "value"
            >>> obj = MyClass()
            >>> ReflectorHelper.get_and_check_object_metadata(obj, "my_meta")
            'value'
            >>> ReflectorHelper.get_and_check_object_metadata(obj, "missing")
            None
        """

        if cls.object_has_metadata(object_, meta_data_name, meta_obj_type):
            return getattr(object_, meta_data_name)

        return None

    @classmethod
    def set_object_has_metadata(cls, object_: Any, meta_data_name: str, value: Any) -> None:
        """Set metadata on an object.

        Dynamically adds or updates a metadata attribute on the given object.

        :param object_: The object to set metadata on
        :type object_: Any
        :param meta_data_name: The name of the metadata attribute to set
        :type meta_data_name: str
        :param value: The value to assign to the metadata attribute
        :type value: Any

        Example:
            >>> obj = MyClass()
            >>> ReflectorHelper.set_object_has_metadata(obj, "custom_meta", "my_value")
            >>> obj.custom_meta
            'my_value'
        """
        setattr(object_, meta_data_name, value)

    @classmethod
    def get_method_named_args_json(cls, method: Any) -> list[MethodArgDoc]:
        """Convert method arguments to JSON-serializable documentation format.

        Extracts and formats method argument information into a list of MethodArgDoc
        objects suitable for JSON serialization. Handles type annotations, default
        values, and type inference.

        :param method: The method to extract argument documentation from
        :type method: Any
        :return: List of argument documentation objects
        :rtype: List[MethodArgDoc]

        Note:
            - Infers types from default values when annotations are missing
            - Handles empty string default values specially
            - Converts all default values to string representation
        """
        arguments: dict[str, FuncArgMetaData] = cls.get_function_arguments(method).get_named_args()
        arguments_json: list[MethodArgDoc] = []
        for arg in arguments.items():
            arg_name: str = arg[0]
            arg_type: Any = arg[1].type_

            arg_default_value: Any = None
            if arg[1].has_default_value():
                arg_default_value = (
                    arg[1].default_value if arg[1].default_value is not None else None
                )

            arg_type = Utils.stringify_type(arg_type)
            if arg_type == "_empty":
                if arg_default_value is not None:
                    arg_type = Utils.stringify_type(type(arg_default_value))
                else:
                    arg_type = "Any"

            if isinstance(arg_default_value, str) and len(arg_default_value) == 0:
                arg_default_value = "''"
            if not isinstance(arg_default_value, str):
                if arg_default_value is None:
                    arg_default_value = ""
                else:
                    arg_default_value = str(arg_default_value)

            arguments_json.append(
                MethodArgDoc(
                    arg_name=arg_name, arg_type=arg_type, arg_default_value=arg_default_value
                )
            )
        return arguments_json

    @classmethod
    def get_func_doc(
        cls, func: Callable[..., Any], type_: type | None = None, func_name: str | None = None
    ) -> MethodDoc | None:
        """Get documentation for a single function.

        :param func: The function to document
        :param type_: Optional type/class to check for method type (classmethod, staticmethod, etc.)
        :param func_name: Optional function name (useful when func is a wrapper and __name__ is incorrect)
        :return: MethodDoc object or None if documentation cannot be generated
        """
        try:
            if not callable(func):
                return None

            method_type: str = MethodDocType.BASICMETHOD
            if func_name is None:
                func_name = func.__name__

            if type_ is not None:
                # Use getattr_static to check for classmethod/staticmethod decorators
                try:
                    static_attr = inspect.getattr_static(type_, func_name)
                    if isinstance(static_attr, classmethod):
                        method_type = MethodDocType.CLASSMETHOD
                    elif isinstance(static_attr, staticmethod):
                        method_type = MethodDocType.STATICMETHOD
                except AttributeError:
                    # If getattr_static fails, method_type remains BASICMETHOD
                    pass

            signature: inspect.Signature = inspect.signature(func)
            arguments = cls.get_method_named_args_json(func)
            return_type = (
                Utils.stringify_type(signature.return_annotation)
                if signature.return_annotation != inspect.Signature.empty
                else None
            )

            doc = cls.get_cleaned_doc_string(func)
            return MethodDoc(
                name=func_name,
                doc=doc,
                args=arguments,
                return_type=return_type,
                method_type=method_type,
            )
        except Exception:
            Logger.error(
                f"Error while getting method doc of {func_name if func_name else 'unknown'}"
            )
            return None

    @classmethod
    def get_all_public_args(cls, type_: type) -> dict[str, str] | None:
        """Get all public type-annotated attributes from a class and its entire inheritance hierarchy.

        Traverses the Method Resolution Order (MRO) to collect all public type-annotated
        attributes from the class and all its parent classes.

        :param type_: The class to inspect
        :type type_: type
        :return: Dictionary mapping attribute names to type strings, or None if not a class
        :rtype: Optional[Dict[str, str]]

        Example:
            >>> class Parent:
            ...     parent_var: str
            >>> class Child(Parent):
            ...     child_var: int
            >>> ReflectorHelper.get_all_public_args(Child)
            {'child_var': 'int', 'parent_var': 'str'}

        Note:
            - Includes attributes from all ancestor classes
            - Returns None if the input is not a class
            - Later classes in MRO can override earlier attributes
        """
        if not inspect.isclass(type_):
            # return None if the type is not a class
            return None

        res = {}
        for class_ in inspect.getmro(type_):
            res.update(cls.get_public_args(class_))
        return res if len(res) > 0 else None

    @classmethod
    def get_public_args(cls, class_) -> dict[str, str]:
        """Get the public type-annotated attributes of a class.

        This method extracts type annotations from a class definition, filtering out
        private attributes (those starting with underscore) and returning them as
        a dictionary mapping attribute names to their type representations.

        :param class_: The class to inspect for annotated attributes
        :type class_: type
        :return: Dictionary mapping public attribute names to their string type representations.
                 Returns empty dict if no annotations are found or if an error occurs.
        :rtype: Dict[str, str]

        Example:
            >>> class MyClass:
            ...     public_var: str
            ...     another_var: int
            ...     _private_var: bool
            >>> ReflectorHelper.get_public_args(MyClass)
            {'another_var': 'int', 'public_var': 'str'}

        Note:
            - Only returns attributes that have type annotations
            - Excludes attributes starting with underscore (_)
            - Returns sorted keys alphabetically
            - Handles both named types (__name__) and complex type hints (converted to string)
        """
        arr_variables = [d for (t, d) in inspect.getmembers(class_) if t == "__annotations__"]

        if len(arr_variables) == 0:
            return {}

        variables = cast(dict, arr_variables[0])
        try:
            vars_keys = sorted(
                [i for i in variables.keys() if i[0] != "_"]
            )  # get the sorted keys of public variables
            res: dict[str, str] = {}
            for k in vars_keys:
                if hasattr(variables[k], "__name__"):
                    res.update({k: variables[k].__name__})
                else:
                    res.update({k: str(variables[k])})
            return res
        except:
            Logger.error(f"Error while getting public args of {class_}")
            return {}

    @classmethod
    def get_public_method_names(cls, type_: type, include_init: bool = False) -> list[str]:
        """Get the names of all public methods of a class.

        :param type_: The class type to inspect
        :param include_init: Whether to include the __init__ method in the results
        :return: List of public method names
        """
        if not inspect.isclass(type_):
            return []

        methods: Any = inspect.getmembers(type_, predicate=inspect.isfunction) + inspect.getmembers(
            type_, predicate=inspect.ismethod
        )

        if include_init:
            return [m[0] for m in methods if not m[0].startswith("_") or m[0] == "__init__"]
        else:
            return [m[0] for m in methods if not m[0].startswith("_")]

    @classmethod
    def get_class_public_methods_doc(
        cls, type_: type, include_init: bool = False
    ) -> list[MethodDoc]:
        """Get documentation for all public methods of a class.

        :param type_: The class type to inspect
        :param include_init: Whether to include the __init__ method in the results
        :return: List of MethodDoc objects for all public methods
        """
        if not inspect.isclass(type_):
            return []

        # Get public method names
        public_method_names = cls.get_public_method_names(type_, include_init=include_init)

        res: list[MethodDoc] = []
        for public_method in public_method_names:
            # Use getattr instead of getattr_static to handle decorated methods properly
            # getattr_static returns wrappers (e.g., deprecated_func), but getattr unwraps them
            method = getattr(type_, public_method)
            # Pass the actual method name to handle cases where wrapper functions have different __name__
            method_doc = cls.get_func_doc(method, type_, func_name=public_method)
            if method_doc is not None:
                res.append(method_doc)
        return res

    @classmethod
    def get_class_docs(cls, type_: type) -> ClassicClassDocDTO | None:
        """Get the cleaned docstring of a class.

        :param type_: The class type to inspect
        :return: Cleaned docstring of the class or None if not available
        """
        if not inspect.isclass(type_):
            return None

        variables = cls.get_all_public_args(type_)
        methods = cls.get_class_public_methods_doc(type_, include_init=True)

        name: str = None
        if not hasattr(type_, "__name__"):
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

        doc = doc.replace("\n# ", "\n## ")

        return doc
