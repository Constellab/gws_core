from enum import Enum


class ScenarioStatus(Enum):
    DRAFT = "DRAFT"
    IN_QUEUE = "IN_QUEUE"  # when the scenario is in Queue waiting to be runned
    # WAITING means that a shell process will be started to run the scenario
    WAITING_FOR_CLI_PROCESS = "WAITING_FOR_CLI_PROCESS"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    PARTIALLY_RUN = "PARTIALLY_RUN"


class ScenarioCreationType(Enum):
    # created by the user
    MANUAL = "MANUAL"
    # Created and executed by the system
    AUTO = "AUTO"
    # Imported from another lab
    IMPORTED = "IMPORTED"


class ScenarioProcessStatus(Enum):
    # if the scenario is not running
    NONE = "NONE"
    # if the scenario is running
    RUNNING = "RUNNING"
    # if the scenario is still running but the process is stopped
    UNEXPECTED_STOPPED = "UNEXPECTED_STOPPED"
