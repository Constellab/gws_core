from ...process.process_factory import ProcessFactory
from ...protocol.protocol_model import ProtocolModel
from ...scenario.queue_service import QueueService
from ...scenario.scenario_service import ScenarioService
from .robot_protocol import RobotSimpleTravel, RobotWorldTravelProto


class RobotService:
    @classmethod
    def run_robot_travel(cls):
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_type(
            protocol_type=RobotSimpleTravel
        )
        protocol.save_full()
        scenario = ScenarioService.create_scenario_from_protocol_model(
            protocol_model=protocol, title="The journey of Astro."
        )
        QueueService.add_scenario_to_queue(scenario_id=scenario.id)
        return scenario

    @classmethod
    def run_robot_super_travel(cls):
        protocol: ProtocolModel = cls.create_robot_world_travel()
        scenario = ScenarioService.create_scenario_from_protocol_model(
            protocol_model=protocol, title="The super journey of Astro."
        )
        QueueService.add_scenario_to_queue(scenario_id=scenario.id)
        return scenario

    @classmethod
    def create_robot_world_travel(cls) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_type(
            protocol_type=RobotWorldTravelProto
        )
        protocol.save_full()
        return protocol

    @classmethod
    def create_robot_simple_travel(cls) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_type(
            protocol_type=RobotSimpleTravel
        )
        protocol.save_full()
        return protocol
