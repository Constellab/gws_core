

from typing import List, Literal, Optional

from typing_extensions import TypedDict

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO


class BrickVersion(BaseModelDTO):
    name: str
    version: Optional[str] = None


class BrickMigrationLogHistory(TypedDict):
    version: str
    migration_date: str


class BrickMigrationLog(TypedDict):
    brick_name: str
    version: str
    last_date_check: str
    history: List[BrickMigrationLogHistory]


class BrickInfo(BaseModelDTO):
    path: str
    name: str
    version: Optional[str]
    repo_type: Optional[Literal['git', 'pip']]
    repo_commit: Optional[str]
    # name of the package that depend on this module
    parent_name: Optional[str]
    error: Optional[str]  # provided if the module could not be loaded


BrickStatus = Literal['SUCCESS', 'ERROR', 'CRITICAL', 'WARNING']
BrickMessageStatus = Literal['INFO', 'ERROR', 'CRITICAL', 'WARNING']


class BrickMessageDTO(BaseModelDTO):
    message: str
    status: BrickMessageStatus
    timestamp: float


class BrickDTO(ModelDTO):
    name: str
    status: BrickStatus
    version: Optional[str] = None
    repo_type: Optional[Literal['git', 'pip']] = None
    brick_path: Optional[str] = None
    repo_commit: Optional[str] = None
    parent_name: Optional[str] = None
    messages: List[BrickMessageDTO]
