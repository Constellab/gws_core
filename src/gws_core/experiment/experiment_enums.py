# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from enum import Enum


class ExperimentStatus(Enum):
    DRAFT = "DRAFT"
    IN_QUEUE = "IN_QUEUE"  # when the experiment is in Queue waiting to be runned
    # WAITING means that a shell process will be started to run the experiment
    WAITING_FOR_CLI_PROCESS = "WAITING_FOR_CLI_PROCESS"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class ExperimentType(Enum):
    # Basic experiment
    EXPERIMENT = "EXPERIMENT"
    # specific experiment generated form a transformer task
    TRANSFORMER = "TRANSFORMER"
    # specific experiment generated form a importer task
    IMPORTER = "IMPORTER"
    # specific experiment generated from a fs node extractor
    FS_NODE_EXTRACTOR = "FS_NODE_EXTRACTOR"