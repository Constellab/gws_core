import os
import sys
from typing import Literal

from typing_extensions import TypedDict

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO


class BrickVersion(BaseModelDTO):
    name: str
    version: str | None = None


class BrickMigrationLogHistory(TypedDict):
    version: str
    migration_date: str


class BrickMigrationLog(TypedDict):
    brick_name: str
    version: str
    last_date_check: str
    history: list[BrickMigrationLogHistory]


class BrickInfo(BaseModelDTO):
    path: str
    name: str
    version: str | None
    repo_type: Literal["git", "pip"] | None
    repo_commit: str | None
    # name of the package that depend on this module
    parent_name: str | None
    error: str | None  # provided if the module could not be loaded

    def get_python_module_path(self) -> str:
        """Returns the python module path of the brick"""
        if self.name not in sys.modules:
            raise ValueError(f"Brick {self.name} is not loaded in the system modules")
        return os.path.dirname(sys.modules[self.name].__path__[0])


BrickStatus = Literal["SUCCESS", "ERROR", "CRITICAL", "WARNING"]
BrickMessageStatus = Literal["INFO", "ERROR", "CRITICAL", "WARNING"]


class BrickMessageDTO(BaseModelDTO):
    message: str
    status: BrickMessageStatus
    timestamp: float


class BrickDTO(ModelDTO):
    name: str
    status: BrickStatus
    version: str | None = None
    repo_type: Literal["git", "pip"] | None = None
    brick_path: str | None = None
    repo_commit: str | None = None
    parent_name: str | None = None
    messages: list[BrickMessageDTO]


class BrickDirectoryDTO(BaseModelDTO):
    """DTO representing a brick directory"""

    name: str
    path: str
    # Either the brick is in the system folder or in the user folder
    folder: Literal["system", "user"]
