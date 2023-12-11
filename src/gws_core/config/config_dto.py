# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.core.model.model_with_user_dto import ModelWithUserDTO


class ConfigDTO(ModelWithUserDTO):
    """
    ConfigDTO class.
    """
    specs: dict
    values: dict
