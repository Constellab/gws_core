# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.process.processable_factory import ProcessableFactory
from gws_core.protocol import protocol_type

from ...core.service.base_service import BaseService
from ...experiment.experiment_service import ExperimentService
from ...experiment.queue_service import QueueService
from .robot import RobotWorldTravelProto, create_protocol


class RobotService(BaseService):

    @classmethod
    def run_robot_travel(cls):
        protocol = create_protocol()
        experiment = ExperimentService.create_experiment_from_protocol(protocol=protocol,
                                                                       title="The journey of Astro.",
                                                                       description="This is the journey of Astro.")
        QueueService.add_experiment_to_queue(experiment_uri=experiment.uri)
        return experiment

    @classmethod
    def run_robot_super_travel(cls):
        protocol = cls.create_nested_protocol()
        experiment = ExperimentService.create_experiment_from_protocol(protocol=protocol,
                                                                       title="The super journey of Astro.",
                                                                       description="This is the super journey of Astro.")
        QueueService.add_experiment_to_queue(experiment_uri=experiment.uri)
        return experiment

    @classmethod
    def create_nested_protocol(cls) -> RobotWorldTravelProto:
        return ProcessableFactory.create_protocol_from_type(protocol_type=RobotWorldTravelProto)
