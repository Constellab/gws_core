# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from fastapi import Depends

from gws_core.experiment.experiment_dto import ExperimentDTO
from gws_core.experiment.queue_dto import JobDTO
from gws_core.experiment.queue_service import QueueService
from gws_core.user.auth_service import AuthService

from ..core_controller import core_app


@core_app.get("/queue/jobs", tags=["Queue"], summary="Get the list of job of main queue")
def get_the_experiment_queue(_=Depends(AuthService.check_user_access_token)) -> List[JobDTO]:
    """
    Retrieve the queue of experiments
    """

    queue_job = QueueService.get_queue_jobs()
    return [job.to_dto() for job in queue_job]


@core_app.delete("/queue/experiment/{id}", tags=["Queue"], summary="Get the queue of experiments")
def remove_experiment_from_queue(
        id: str,
        _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Remove an experiment from the queue
    """

    return QueueService.remove_experiment_from_queue(id).to_dto()
