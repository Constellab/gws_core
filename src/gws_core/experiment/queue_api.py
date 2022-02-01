from fastapi import Depends
from gws_core.core.classes.jsonable import ListJsonable
from gws_core.experiment.queue_service import QueueService
from gws_core.user.auth_service import AuthService
from gws_core.user.user_dto import UserData

from ..core_app import core_app


@core_app.get("/queue/jobs", tags=["Queue"], summary="Get the list of job of main queue")
def get_the_experiment_queue(_: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve the queue of experiments
    """

    return ListJsonable(QueueService.get_queue_jobs()).to_json()


@core_app.delete("/queue/experiment/{id}", tags=["Queue"], summary="Get the queue of experiments")
def remove_experiment_from_queue(
        id: str,
        _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Remove an experiment from the queue
    """

    return QueueService.remove_experiment_from_queue(id).to_json()
