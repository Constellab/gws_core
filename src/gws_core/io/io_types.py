

from typing import Dict, Tuple, Type, Union

from ..resource.resource import Resource

IOSpec = Union[Type[Resource], Tuple[Type[Resource]]]
IOSpecs = Dict[str, IOSpec]
