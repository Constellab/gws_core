
# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import inspect
from typing import Any, Dict, Type, Union

EmptyClass: Type = inspect.Signature.empty


class FuncArgMetaData():
    """Class to manipulate a specific argument of a function metadata

    :return: [description]
    :rtype: [type]
    """
    arg_name: str
    default_value: Union[Any, EmptyClass]
    type_: Union[Type, EmptyClass]

    def __init__(self, arg_name: str, default_value: Any, type_: Type) -> None:
        self.arg_name = arg_name
        self.default_value = default_value
        self.type_ = type_

    def has_default_value(self) -> bool:
        return not inspect.isclass(self.default_value) or not issubclass(self.default_value, EmptyClass)

    def has_type(self) -> bool:
        return not issubclass(self.type_, EmptyClass)


class FuncArgsMetaData():
    """Class to manipulate fun args metadata

    :return: [description]
    :rtype: [type]
    """

    func_name: str
    args: Dict[str, FuncArgMetaData]

    def __init__(self, func_name: str) -> None:
        self.func_name = func_name
        self.args = {}

    def add_arg(self, arg_name: str, meta_data: FuncArgMetaData) -> None:
        self.args[arg_name] = meta_data

    def all_args_have_default(self) -> bool:
        for arg_name, arg in self.args.items():
            if arg_name == 'self' or arg_name == 'cls':
                continue
            if not arg.has_default_value():
                return False
        return True

    def is_method(self) -> bool:
        return 'self' in self.args

    def is_class_method(self) -> bool:
        return 'cls' in self.args
