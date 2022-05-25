# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from abc import abstractmethod
from collections.abc import Iterable as IterableClass
from typing import Iterable, List, Optional, Tuple, Type, TypedDict, Union

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.utils.utils import Utils
from gws_core.model.typing_dict import TypingRef

from ..model.typing_manager import TypingManager
from ..resource.resource import Resource

ResourceType = Type[Resource]
ResourceTypes = Union[ResourceType, Iterable[ResourceType]]


class IOSpecDict(TypedDict):
    io_spec: str
    resource_types: List[TypingRef]
    human_name: Optional[str]
    short_description: Optional[str]
    is_optional: bool
    is_skippable: Optional[bool]
    sub_classsub_class: Optional[bool]
    is_constant: Optional[bool]


class IOSpec:
    resource_types: List[ResourceType]

    # Human readable name of the param, showed in the interface
    human_name: Optional[str]

    # Description of the param, showed in the interface
    short_description: Optional[str]

    is_optional: bool = False

    _name: str = "IOSpec"   # unique name to distinguish the types, do not modify

    def __init__(self, resource_types: ResourceTypes, is_optional: bool = False, human_name: Optional[str] = None,
                 short_description: Optional[str] = None) -> None:
        """[summary]

        :param resource_types: type of supported resource or resources
        :type resource_types: Type[Union[Resource, Iterable[Resource]]]
        """

        self.resource_types = []
        if not isinstance(resource_types, IterableClass):
            self.resource_types.append(resource_types)
        else:
            for r_type in resource_types:
                self.resource_types.append(r_type)

        self.is_optional = is_optional

        self.check_resource_types()

        # TODO Remove support for None
        default_type = self.get_default_resource_type()

        # set the human name with a default value
        if human_name is not None:
            self.human_name = Utils.snake_case_to_sentence(human_name)
        else:
            # TODO Remove support for None
            if default_type:
                self.human_name = default_type._human_name

        # set the short description with a default value
        if short_description is not None:
            self.short_description = short_description
        else:
            # TODO Remove support for None
            if default_type:
                self.short_description = default_type._short_description

    def check_resource_types(self):
        for resource_type in self.resource_types:
            if resource_type is None:
                # TODO Remove support for None
                print("[WARNING] None type will not be supported soon, please set optional parameter to True instead")
                self.is_optional = True
                continue
                # raise Exception(f"Resource type can't be None, please set optional parameter to True instead")

            if not Utils.issubclass(resource_type, Resource):
                raise Exception(
                    f"Invalid port specs. The type '{resource_type}' used inside the type '{type(self).__name__}' is not a resource")

    def is_compatible_with_in_spec(self, in_spec: 'IOSpec') -> bool:
        # Handle the generic SubClasss
        if self.is_subclass_out():
            # check if type inside the SubClass is compatible with expected type
            # if not check if one of the expected type is compatible with SubClass
            return self._resource_types_are_compatible(
                resource_types=self.resource_types, expected_types=in_spec.resource_types) or self._resource_types_are_compatible(
                resource_types=in_spec.resource_types, expected_types=self.resource_types)

        return self._resource_types_are_compatible(
            resource_types=self.resource_types, expected_types=in_spec.resource_types)

    def is_compatible_with_resource_type(self, resource_type: Type[Resource]) -> bool:
        return self._resource_types_are_compatible(resource_types=[resource_type], expected_types=self.resource_types)

    @abstractmethod
    def is_constant_out(self) -> bool:
        pass

    @abstractmethod
    def is_skippable_in(self) -> bool:
        pass

    @abstractmethod
    def is_subclass_out(self) -> bool:
        pass

    def get_default_resource_type(self) -> Type[Resource]:
        """return the first default type
        """
        return self.resource_types[0]

    def get_resource_type_tuples(self) -> Tuple[Type[Resource]]:
        return tuple(self.resource_types)

    def get_resources_human_names(self) -> str:
        list_str = [(resource_type._human_name if resource_type else 'None') for resource_type in self.resource_types]

        if len(list_str) == 1:
            return list_str[0]
        else:
            return ', '.join(list_str)

    @classmethod
    def _resource_types_are_compatible(cls, resource_types: Iterable[Type[Resource]],
                                       expected_types: Iterable[Type[Resource]]) -> bool:

        for resource_type in resource_types:
            if cls._resource_types_is_compatible(
                    resource_type=resource_type, expected_types=expected_types):
                return True

        return False

    @classmethod
    def _resource_types_is_compatible(cls, resource_type: Type[Resource],
                                      expected_types: Iterable[Type[Resource]]) -> bool:

        # check that the resource type is a subclass of one of the port resources types
        for expected_type in expected_types:
            if issubclass(resource_type, expected_type):
                return True

        return False

    def to_json(self) -> IOSpecDict:
        json_: IOSpecDict = {"resource_types": [],
                             "is_optional": self.is_optional,
                             "human_name": self.human_name, "short_description": self.short_description}
        for resource_type in self.resource_types:
            typing = TypingManager.get_typing_from_name(resource_type._typing_name)
            resource_json: TypingRef = {"typing_name": typing.typing_name,
                                        "brick_version": str(BrickHelper.get_brick_version(typing.brick)),
                                        "human_name": typing.human_name}

            json_["resource_types"].append(resource_json)
        return json_

    @classmethod
    def from_json(cls, json_: IOSpecDict) -> 'IOSpec':

        resource_types: List[ResourceType] = []

        # retrieve all the resource type from the json specs
        for spec_json in json_['resource_types']:
            resource_types.append(TypingManager.get_type_from_name(spec_json['typing_name']))

        io_spec: IOSpec = cls(resource_types=resource_types, is_optional=json_.get('is_optional', False),
                              human_name=json_.get('human_name'),
                              short_description=json_.get('short_description'),)
        return io_spec


class InputSpec(IOSpec):
    """ Spec for an input task port
    """
    _name: str = "InputSpec"

    _is_skippable: bool

    def __init__(self, resource_types: ResourceTypes,
                 is_optional: bool = False,
                 is_skippable: bool = False,
                 human_name: Optional[str] = None,
                 short_description: Optional[str] = None) -> None:
        """_summary_

        :param resource_types: _description_
        :type resource_types: ResourceTypes
        :param is_optional: _description_, defaults to False
        :type is_optional: bool, optional
        :param is_skippable: When true, this tells the system that the input is skippable. This mean that the task can be called
                  even if this input was connected and the value no provided.
                  With this you can run your task even if the input value was not received
                  //!\\ WARNING If an input is skipped, the input is not set, the inputs['name'] will raise a KeyError exception (different from None)
                  Has no effect when there is only one input, defaults to False
        :type is_skippable: bool, optional
        :param human_name: _description_, defaults to None
        :type human_name: Optional[str], optional
        :param short_description: _description_, defaults to None
        :type short_description: Optional[str], optional
        """
        # if the input is skippable force it to be optional
        if is_skippable:
            is_optional = True

        super().__init__(resource_types=resource_types, is_optional=is_optional,
                         human_name=human_name, short_description=short_description)
        self._is_skippable = is_skippable

    def is_constant_out(self) -> bool:
        return False

    def is_skippable_in(self) -> bool:
        return self._is_skippable

    def is_subclass_out(self) -> bool:
        return False

     # Add the sub class attribute

    def to_json(self) -> IOSpecDict:
        json_ = super().to_json()
        json_["is_skippable"] = self._is_skippable

        return json_

    @classmethod
    def from_json(cls, json_: IOSpecDict) -> 'OutputSpec':
        input_spec: InputSpec = super().from_json(json_)
        input_spec._is_skippable = json_.get('is_skippable', False)

        # TODO TO REMOVE For retropcompatibility
        if json_.get('io_spec') == 'OptionalIn' or json_.get('type_io') == 'OptionalIn':
            input_spec.is_optional = True

        if json_.get('io_spec') == 'SkippableIn' or json_.get('type_io') == 'SkippableIn':
            input_spec._is_skippable = True
        return input_spec


class OutputSpec(IOSpec):
    """ Spec for an output task port
    """
    _name: str = "OutputSpec"

    _sub_class: bool
    _is_constant: bool

    def __init__(self, resource_types: ResourceTypes,
                 is_optional: bool = False,
                 sub_class: bool = False,
                 is_constant: bool = False,
                 human_name: Optional[str] = None,
                 short_description: Optional[str] = None) -> None:
        """_summary_

        :param resource_types: _description_
        :type resource_types: ResourceTypes
        :param is_optional: _description_, defaults to False
        :type is_optional: bool, optional
        :param sub_class: When true, it tells that the resource_types
                are compatible with any child class of the provided resource type, defaults to False
        :param is_constant: When true, this tells the system that the output resource was not modified from the input resource
              and it does not need to create a new resource after the task, defaults to False
        :param human_name: _description_, defaults to None
        :type human_name: Optional[str], optional
        :param short_description: _description_, defaults to None
        :type short_description: Optional[str], optional
        """

        super().__init__(resource_types=resource_types, is_optional=is_optional,
                         human_name=human_name, short_description=short_description)
        self._sub_class = sub_class
        self._is_constant = is_constant

    def is_constant_out(self) -> bool:
        return self._is_constant

    def is_skippable_in(self) -> bool:
        return False

    def is_subclass_out(self) -> bool:
        return self._sub_class

    # Add the sub class attribute
    def to_json(self) -> IOSpecDict:
        json_ = super().to_json()
        json_["sub_class"] = self._sub_class
        json_["is_constant"] = self._is_constant

        return json_

    @classmethod
    def from_json(cls, json_: IOSpecDict) -> 'OutputSpec':
        output_spec: OutputSpec = super().from_json(json_)
        output_spec._sub_class = json_.get('sub_class', False)
        output_spec._is_constant = json_.get('is_constant', False)

        # TODO TO REMOVE For retropcompatibility
        if json_.get('io_spec') == 'ConstantOut' or json_.get('type_io') == 'ConstantOut':
            output_spec._is_constant = True

        if "data" in json_ and json_.get('data').get('sub_class'):
            output_spec._sub_class = True
        return output_spec


class OptionalIn(InputSpec):
    """Special type to use in Input specs
    This type tell the system that the input is optional.
    The input can be not connected and the task will still run (the input value will then be None)
    If the input is connected, the task will wait for the resource to run himself (this is the difference from SkippableIn)
    """

    def __init__(self, resource_types: ResourceTypes, is_optional: bool = True, human_name: Optional[str] = None,
                 short_description: Optional[str] = None) -> None:
        super().__init__(resource_types=resource_types, is_optional=is_optional,
                         human_name=human_name, short_description=short_description)
        print('[WARNING] OptionalIn is deprecated, please use InputSpec with is_optional=True instead')


class SkippableIn(InputSpec):
    """Special type to use in Input specs
    This type tell the system that the input is skippable. This mean that the task can be called
    even if this input was connected and the value no provided.
    With this you can run your task even if the input vaue was not received
    //!\\ WARNING If an input is skipped, the input is not set, the inputs['name'] will raise a KeyError exception (different from None)

    Has no effect when there is only one input

    """

    def __init__(self, resource_types: ResourceTypes, is_optional: bool = True, human_name: Optional[str] = None,
                 short_description: Optional[str] = None) -> None:
        super().__init__(resource_types=resource_types, is_optional=is_optional,
                         human_name=human_name, short_description=short_description)
        print('[WARNING] SkippableIn is deprecated, please use InputSpec with is_skippable=True instead')


class ConstantOut(OutputSpec):
    """Special type to use in Output specs
    This type tells the system that the output resource was not modified from the input resource
    and it does not need to create a new resource after the task
    """

    def __init__(self, resource_types: ResourceTypes, is_optional: bool = False, sub_class: bool = False,
                 human_name: Optional[str] = None, short_description: Optional[str] = None) -> None:
        super().__init__(resource_types=resource_types, is_optional=is_optional, sub_class=sub_class,
                         human_name=human_name, short_description=short_description)
        self._is_constant = True
        print('[WARNING] ConstantOut is deprecated, please use OutputSpec with is_constant=True instead')
