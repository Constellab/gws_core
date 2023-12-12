# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Optional

from gws_core.io.io_spec import IOSpecDTO
from gws_core.model.typing_dto import TypingFullDTO


class TaskTypingDTO(TypingFullDTO):
    input_specs: Optional[IOSpecDTO] = None
    output_specs: Optional[IOSpecDTO] = None
    # TODO imrove typing
    config_specs: Optional[dict] = None
    additional_data: Optional[dict] = None
