
from typing import Literal

from typing_extensions import TypedDict

SupportedDbEngine = Literal['mysql', 'mariadb']

DbMode = Literal['prod', 'dev', 'test']


class DbConfig(TypedDict):
    user: str
    password: str
    host: str
    port: int
    db_name: str
    engine: SupportedDbEngine
