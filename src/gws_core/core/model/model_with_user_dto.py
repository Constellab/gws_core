# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.core.model.model_dto import ModelDTO
from gws_core.user.user_dto import UserDTO


class ModelWithUserDTO(ModelDTO):
    """
    ModelWithUserDTO class.
    """
    created_by: UserDTO
    last_modified_by: UserDTO
