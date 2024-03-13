
from enum import Enum


class ExperimentStatus(Enum):
    DRAFT = "DRAFT"
    IN_QUEUE = "IN_QUEUE"  # when the experiment is in Queue waiting to be runned
    # WAITING means that a shell process will be started to run the experiment
    WAITING_FOR_CLI_PROCESS = "WAITING_FOR_CLI_PROCESS"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    PARTIALLY_RUN = "PARTIALLY_RUN"


class ExperimentCreationType(Enum):
    # created by the user
    MANUAL = "MANUAL"
    # Created and executed by the system
    AUTO = "AUTO"


class ExperimentProcessStatus(Enum):
    # if the experiment is not running
    NONE = "NONE"
    # if the experiment is running
    RUNNING = "RUNNING"
    # if the experiment is still running but the process is stopped
    UNEXPECTED_STOPPED = "UNEXPECTED_STOPPED"
