import os
import re
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
    variables: dict | None = None

    def get_python_module_path(self) -> str:
        """Returns the python module path of the brick"""
        if self.name not in sys.modules:
            raise ValueError(f"Brick {self.name} is not loaded in the system modules")
        return os.path.dirname(sys.modules[self.name].__path__[0])

    def get_variable(self, key: str) -> str | None:
        """Returns a variable for this brick. Returns `None` if the variable does not exist"""
        if not self.variables:
            return None
        return self._expand_environment_variables(self.variables.get(key))

    def _expand_environment_variables(self, variable: str | None) -> str | None:
        """Expand environment variable references in a configuration string.

        Replaces environment variable patterns like $VAR_NAME or ${VAR_NAME} with their
        actual values from the system environment. Only matches uppercase letters and
        underscores (standard environment variable naming convention).

        :param variable: The string potentially containing environment variable references
        :type variable: str
        :return: The string with environment variables expanded, or the original if no matches
        :rtype: str

        :example:
            >>> # Assuming LAB_ID="12345" in environment
            >>> self._expand_environment_variables("Lab ID is $LAB_ID")
            'Lab ID is 12345'
            >>> self._expand_environment_variables("Path: ${HOME}/data")
            'Path: /home/user/data'
        """
        if not variable:
            return variable

        tabs = re.findall(r"\$\{?([A-Z_]*)\}?", variable)
        for token in tabs:
            value = os.getenv(token)
            if value:
                variable = re.sub(r"\$\{?" + token + r"\}?", value, variable)
        return variable


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
