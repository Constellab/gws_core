from enum import Enum


class TriggerType(Enum):
    """Type of trigger for a job"""
    CRON = "CRON"


class JobRunTrigger(Enum):
    """How the job run was triggered"""
    CRON = "CRON"           # Triggered by the scheduler
    MANUAL = "MANUAL"       # Triggered manually via API


class JobStatus(Enum):
    """Status of a job execution"""
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class TriggeredJobSource(Enum):
    """How the triggered job was created"""
    DECORATOR = "DECORATOR"  # Created via @cron_job_decorator on a Task/Protocol
    MANUAL = "MANUAL"        # Created dynamically via API or code
