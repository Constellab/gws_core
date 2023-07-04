# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from .io_spec import InputSpec, OutputSpec
from .io_specs import InputSpecs, OutputSpecs


class DynamicInputs(InputSpecs):

    def __init__(self, default_specs: Dict[str, InputSpec] = None) -> None:
        super().__init__(default_specs)

    def is_dynamic(self) -> bool:
        return True


class DynamicOutputs(OutputSpecs):

    def __init__(self, default_specs: Dict[str, OutputSpec] = None) -> None:
        super().__init__(default_specs)

    def is_dynamic(self) -> bool:
        return True
