

from typing import Dict, Iterable, List, Type, TypedDict, Union

from ..resource.resource import Resource

IOSpec = Union[Type[Resource], Iterable[Type[Resource]]]
IOSpecs = Dict[str, IOSpec]


class PortResourceDict(TypedDict):
    uri: str
    typing_name: str


class PortDict(TypedDict):
    resource: PortResourceDict
    specs: List[str]  # list of supported resource typing names


IODict = Dict[str, PortDict]
