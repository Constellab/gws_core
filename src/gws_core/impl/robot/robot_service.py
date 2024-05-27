

from ...experiment.experiment_service import ExperimentService
from ...experiment.queue_service import QueueService
from ...process.process_factory import ProcessFactory
from ...protocol.protocol_model import ProtocolModel
from .robot_protocol import RobotSimpleTravel, RobotWorldTravelProto


class RobotService():

    @classmethod
    def run_robot_travel(cls):
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_type(
            protocol_type=RobotSimpleTravel)
        protocol.save_full()
        experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol_model=protocol, title="The journey of Astro.")
        QueueService.add_experiment_to_queue(experiment_id=experiment.id)
        return experiment

    @classmethod
    def run_robot_super_travel(cls):
        protocol: ProtocolModel = cls.create_robot_world_travel()
        experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol_model=protocol, title="The super journey of Astro.")
        QueueService.add_experiment_to_queue(experiment_id=experiment.id)
        return experiment

    @classmethod
    def create_robot_world_travel(cls) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_type(
            protocol_type=RobotWorldTravelProto)
        protocol.save_full()
        return protocol

    @classmethod
    def create_robot_simple_travel(cls) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_type(
            protocol_type=RobotSimpleTravel)
        protocol.save_full()
        return protocol
