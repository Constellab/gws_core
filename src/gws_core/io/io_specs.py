# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import Dict, TypedDict

from gws_core.io.io_spec import InputSpec, IOSpec, IOSpecDict, OutputSpec


class IOSpecsDict(TypedDict):
    """IOSpecsDict type
    """
    specs: Dict[str, IOSpecDict]
    is_dynamic: bool


class IOSpecs():

    _specs: Dict[str, IOSpec] = {}

    def __init__(self, specs: Dict[str, IOSpec] = None) -> None:
        if specs is None:
            specs = {}
        if not isinstance(specs, dict):
            raise Exception("The specs must be a dictionary")
        self.io_specs = specs

    def get_specs(self) -> Dict[str, IOSpec]:
        return self.io_specs

    def get_spec(self, name: str) -> IOSpec:
        return self.io_specs[name]

    def is_dynamic(self) -> bool:
        return False

    def to_json(self) -> IOSpecsDict:
        """to_json method for IOSpecs
        """

        json_:  IOSpecsDict = {
            "specs": {},
            "is_dynamic": self.is_dynamic()
        }
        for key, spec in self.get_specs().items():
            json_["specs"][key] = spec.to_json()
        return json_


class InputSpecs(IOSpecs):

    _io_specs: Dict[str, InputSpec] = {}

    def __init__(self, input_specs: Dict[str, InputSpec] = None) -> None:
        super().__init__(input_specs)


class OutputSpecs(IOSpecs):

    _io_specs: Dict[str, OutputSpec] = {}

    def __init__(self, output_specs: Dict[str, OutputSpec] = None) -> None:
        super().__init__(output_specs)
