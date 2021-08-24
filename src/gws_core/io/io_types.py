

from typing import Dict, Tuple, Type, Union

from ..resource.resource import Resource

IOSpec = Union[Type[Resource], Tuple[Type[Resource], None]]
IOSpecs = Dict[str, IOSpec]
