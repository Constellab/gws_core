# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ..core.exception import BadRequestException
from ..core.model.study import Study
from ..core.service.base_service import BaseService
from ..experiment.queue import Job
from ..experiment.queue_service import QueueService
from ..robot.robot import create_nested_protocol, create_protocol
from ..user.current_user_service import CurrentUserService


class AstroService(BaseService):

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
        protocol = create_nested_protocol()
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