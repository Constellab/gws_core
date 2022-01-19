# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import ResourceModel
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.io.connector import Connector
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.resource.resource_model import ResourceOrigin
from gws_core.task.plug import Sink, Source
from gws_core.test.base_test_case import BaseTestCase


class TestProtocolService(BaseTestCase):

    def test_add_process(self):
        protocol_model: ProtocolModel = ProtocolService.create_empty_protocol()

        process_model: ProcessModel = ProtocolService.add_process_to_protocol_id(
            protocol_model.id, RobotMove._typing_name)

        protocol_model = protocol_model.refresh()
        self.assertEqual(protocol_model.get_process(process_model.instance_name).get_process_type(), RobotMove)

        # Test add source
        resource_model: ResourceModel = ResourceModel.save_from_resource(Robot.empty(), ResourceOrigin.UPLOADED)
        source_model: ProcessModel = ProtocolService.add_source_to_process_input(
            protocol_model.id, process_model.instance_name, 'robot', resource_model.id).process_model

        protocol_model = protocol_model.refresh()
        source_model = protocol_model.get_process(source_model.instance_name)
        self.assertEqual(source_model.get_process_type(), Source)
        self.assertEqual(source_model.config.get_value('resource_id'), resource_model.id)

        # Check that the connector was created
        self.assertEqual(len(protocol_model.connectors), 1)

        # Test add sink
        sink_model: ProcessModel = ProtocolService.add_sink_to_process_ouput(
            protocol_model.id, process_model.instance_name, 'robot').process_model
        protocol_model = protocol_model.refresh()
        sink_model = protocol_model.get_process(sink_model.instance_name)
        self.assertEqual(sink_model.get_process_type(), Sink)

        # Check that the connector was created
        self.assertEqual(len(protocol_model.connectors), 2)

    def test_connector(self):
        protocol_model: ProtocolModel = ProtocolService.create_empty_protocol()

        create: ProcessModel = ProtocolService.add_process_to_protocol_id(
            protocol_model.id, RobotCreate._typing_name)
        move: ProcessModel = ProtocolService.add_process_to_protocol_id(
            protocol_model.id, RobotMove._typing_name)

        ProtocolService.add_connector_to_protocol_id(
            protocol_model.id, create.instance_name, 'robot', move.instance_name, 'robot')

        protocol_model = protocol_model.refresh()

        # Check that the connector was created
        self.assertEqual(len(protocol_model.connectors), 1)
        connector: Connector = protocol_model.connectors[0]

        # Check the port of the connector
        self.assertEqual(connector.out_port.name, 'robot')
        self.assertEqual(connector.out_port.parent.parent.id, create.id)
        self.assertEqual(connector.in_port.name, 'robot')
        self.assertEqual(connector.in_port.parent.parent.id, move.id)

        # Test removing connector
        ProtocolService.delete_connector_of_protocol(protocol_model.id, move.instance_name, 'robot')

        protocol_model = protocol_model.refresh()

        # Check that the connector was deleted
        self.assertEqual(len(protocol_model.connectors), 0)
