# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...core.exception.exceptions import BadRequestException
from ...core.service.base_service import BaseService
from ...experiment.queue_service import QueueService
from ...study.study import Study
from ...user.current_user_service import CurrentUserService
from .robot import RobotWorldTravelProto, create_protocol


class RobotService(BaseService):

    @classmethod
    def run_robot_travel(cls):
        user = CurrentUserService.get_and_check_current_user()
        study = Study.get_default_instance()
        protocol = create_protocol()
        experiment = protocol.create_experiment(study=study, user=user)
        experiment.set_title("The journey of Astro.")
        experiment.data["description"] = "This is the journey of Astro."
        experiment.save()
        try:
            QueueService.add_experiment_to_queue(experiment_uri=experiment.uri)
            return experiment
        except Exception as err:
            raise BadRequestException(
                detail="Cannot run robot_travel") from err

    @classmethod
    def run_robot_super_travel(cls):
        user = CurrentUserService.get_and_check_current_user()
        study = Study.get_default_instance()
        protocol = cls.create_nested_protol()
        experiment = protocol.create_experiment(study=study, user=user)
        experiment.set_title("The super journey of Astro.")
        experiment.data["description"] = "This is the super journey of Astro."
        experiment.save()

        try:
            QueueService.add_experiment_to_queue(experiment_uri=experiment.uri)
            return experiment
        except Exception as err:
            raise BadRequestException(
                detail="Cannot run robot_super_travel.") from err

    @classmethod
    def create_nested_protol(cls) -> RobotWorldTravelProto:
        return RobotWorldTravelProto()
