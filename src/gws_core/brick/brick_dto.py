# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Literal, Optional

from typing_extensions import TypedDict


class BrickVersion(TypedDict):
    name: str
    version: str


class BrickMigrationLogHistory(TypedDict):
    version: str
    migration_date: str


class BrickMigrationLog(TypedDict):
    brick_name: str
    version: str
    last_date_check: str
    history: List[BrickMigrationLogHistory]


class BrickInfo(TypedDict):
    path: str
    name: str
    version: str
    repo_type: Literal['git', 'pip']
    repo_commit: Optional[str]
    # name of the package that depend on this module
    parent_name: Optional[str]
    error: Optional[str]  # provided if the module could not be loaded
