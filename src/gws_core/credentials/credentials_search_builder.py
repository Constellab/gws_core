from ..core.classes.search_builder import SearchBuilder
from .credentials import Credentials


class CredentialsSearchBuilder(SearchBuilder):
    def __init__(self) -> None:
        super().__init__(Credentials, default_orders=[Credentials.name.asc()])
