# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ..config.config_spec import ConfigSpecs
from ..core.model.base import Base
from ..user.user_group import UserGroup


class Processable(Base):

    # Config spec of the processable at the class level
    config_specs: ConfigSpecs = {}

    # Provided at the Class level automatically by the Decorator
    # //!\\ Do not modify theses values
    _typing_name: str = None
    _human_name: str = None
    _short_description: str = None
    _allowed_user: UserGroup = UserGroup.USER
