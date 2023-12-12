# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.core.model.model_dto import BaseModelDTO


class MigrationDTO(BaseModelDTO):
    version: str
    short_description: str
