# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from gws_core.core.service.front_service import FrontService

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..process.process_exception import ProcessRunException

if TYPE_CHECKING:
    from .experiment import Experiment


class ExperimentRunException(BadRequestException):
    """Generic exception to raised from another exception during the process run
    It show the original error and provided debug information about the process and experiment

    :param BadRequestException: [description]
    :type BadRequestException: [type]
    """

    original_exception: Exception
    experiment: Experiment

    def __init__(self, experiment: Experiment, exception_detail: str,
                 unique_code: str, instance_id: str, exception: Exception) -> None:
        self.original_exception = exception
        self.experiment = experiment

        detail_arg: Dict = {"error": exception_detail, "experiment": experiment.id}
        super().__init__(
            GWSException.EXPERIMENT_RUN_EXCEPTION.value,
            unique_code=unique_code,
            detail_args=detail_arg,
            instance_id=instance_id)

    @staticmethod
    def from_exception(experiment: Experiment, exception: Exception) -> ExperimentRunException:

        unique_code: str
        instance_id: str

        # create from a know exception
        if isinstance(exception, ProcessRunException):
            unique_code = exception.unique_code
            instance_id = exception.instance_id
        else:
            unique_code = GWSException.EXPERIMENT_RUN_EXCEPTION.name
            instance_id = None

        return ExperimentRunException(
            experiment=experiment, exception_detail=str(exception),
            unique_code=unique_code, instance_id=instance_id, exception=exception)


class ResourceUsedInAnotherExperimentException(BadRequestException):
    def __init__(self, resource_model_name: str, resource_id: str,
                 experiment_name: str, experiment_id: str) -> None:
        super().__init__(
            GWSException.RESET_ERROR_RESOURCE_USED_IN_ANOTHER_EXPERIMENT.value,
            unique_code=GWSException.RESET_ERROR_RESOURCE_USED_IN_ANOTHER_EXPERIMENT.name,
            detail_args={
                "resource_model_name": resource_model_name,
                "resource_url": FrontService.get_resource_url(resource_id),
                "experiment": experiment_name,
                "experiment_url": FrontService.get_experiment_url(experiment_id)
            })
