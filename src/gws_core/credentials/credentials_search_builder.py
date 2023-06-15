# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ..core.classes.search_builder import SearchBuilder
from .credentials import Credentials


class CredentialsSearchBuilder(SearchBuilder):

    def __init__(self) -> None:
        super().__init__(Credentials, default_orders=[Credentials.name.asc()])
