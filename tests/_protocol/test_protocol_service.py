# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import ResourceModel
from gws_core.experiment.experiment_exception import \
    ResourceUsedInAnotherExperimentException
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.impl.live.py_live_task import PyLiveTask
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.io.connector import Connector
from gws_core.io.io_spec import IOSpecDict
from gws_core.model.typing import Typing
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_interface import IProtocol
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.resource.resource import Resource
from gws_core.resource.resource_model import ResourceOrigin
from gws_core.resource.view.viewer import Viewer
from gws_core.task.plug import Sink, Source
from gws_core.task.task_model import TaskModel
from gws_core.test.base_test_case import BaseTestCase
from tests.protocol_examples import TestNestedProtocol, TestSimpleProtocol


# test_protocol_service
class TestProtocolService(BaseTestCase):

    def test_add_process(self):
        protocol_model: ProtocolModel = ProtocolService.create_empty_protocol()

        process_model: ProcessModel = ProtocolService.add_process_to_protocol_id(
            protocol_model.id, RobotMove._typing_name).process

        protocol_model = protocol_model.refresh()
        self.assertEqual(protocol_model.get_process(
            process_model.instance_name).get_process_type(), RobotMove)

        # Test add source
        resource_model: ResourceModel = ResourceModel.save_from_resource(
            Robot.empty(), ResourceOrigin.UPLOADED)
        source_model: ProcessModel = ProtocolService.add_source_to_process_input(
            protocol_model.id, resource_model.id, process_model.instance_name, 'robot').process

        protocol_model = protocol_model.refresh()
        source_model: TaskModel = protocol_model.get_process(
            source_model.instance_name)
        self.assertEqual(source_model.get_process_type(), Source)
        self.assertEqual(source_model.config.get_value(
            Source.config_name), resource_model.id)
        # check that the source_config_id is set for the task model
        self.assertEqual(source_model.source_config_id, resource_model.id)
        # Check that the source was automatically run
        self.assertTrue(source_model.is_finished)

        # check that the robot_move received the resource because Source was run
        process_model = process_model.refresh()
        self.assertEqual(process_model.in_port('robot').resource_model.id, resource_model.id)

        # Check that the connector was created
        self.assertEqual(len(protocol_model.connectors), 1)

        # Test add sink
        sink_model: ProcessModel = ProtocolService.add_sink_to_process_ouput(
            protocol_model.id, process_model.instance_name, 'robot').process
        protocol_model = protocol_model.refresh()
        sink_model = protocol_model.get_process(sink_model.instance_name)
        self.assertEqual(sink_model.get_process_type(), Sink)

        # Check that the connector was created
        self.assertEqual(len(protocol_model.connectors), 2)

    def test_add_viewer(self):
        protocol_model: ProtocolModel = ProtocolService.create_empty_protocol()

        process_model: ProcessModel = ProtocolService.add_process_to_protocol_id(
            protocol_model.id, RobotMove._typing_name).process

        # Test add view task
        viewer_model = ProtocolService.add_viewer_to_process_output(
            protocol_model.id, process_model.instance_name, 'robot').process
        protocol_model = protocol_model.refresh()

        viewer_model = protocol_model.get_process(viewer_model.instance_name)
        self.assertEqual(viewer_model.get_process_type(), Viewer)
        # check that the view task was pre-configured with the robot type
        self.assertEqual(viewer_model.config.get_value(
            Viewer.resource_config_name), Robot._typing_name)

        # Check that the connector was created
        self.assertEqual(len(protocol_model.connectors), 1)

    def test_connector(self):
        protocol_model: ProtocolModel = ProtocolService.create_empty_protocol()

        create: ProcessModel = ProtocolService.add_process_to_protocol_id(
            protocol_model.id, RobotCreate._typing_name).process
        move: ProcessModel = ProtocolService.add_process_to_protocol_id(
            protocol_model.id, RobotMove._typing_name).process

        ProtocolService.add_connector_to_protocol_id(
            protocol_model.id, create.instance_name, 'robot', move.instance_name, 'robot')

        protocol_model = protocol_model.refresh()

        # Check that the connector was created
        self.assertEqual(len(protocol_model.connectors), 1)
        connector: Connector = protocol_model.connectors[0]

        # Check the port of the connector
        self.assertEqual(connector.left_port_name, 'robot')
        self.assertEqual(connector.left_process.id, create.id)
        self.assertEqual(connector.right_port_name, 'robot')
        self.assertEqual(connector.right_process.id, move.id)

        # Test removing connector
        ProtocolService.delete_connector_of_protocol(
            protocol_model.id, move.instance_name, 'robot')

        protocol_model = protocol_model.refresh()

        # Check that the connector was deleted
        self.assertEqual(len(protocol_model.connectors), 0)

    def test_reset_process(self):

        experiment = IExperiment(TestNestedProtocol)
        experiment.run()
        self.assertTrue(experiment.get_experiment_model().is_success)

        # reset a process of the sub protocol
        main_protocol: IProtocol = experiment.get_protocol()
        sub_protocol: IProtocol = main_protocol.get_process('mini_proto')

        # Get resources and check that they exist
        main_resource_to_clear: ResourceModel = main_protocol.get_process(
            'p5').get_output_resource_model('robot')
        sub_resource_to_keep: ResourceModel = sub_protocol.get_process(
            'p1').get_output_resource_model('robot')
        sub_resource_to_clear: ResourceModel = sub_protocol.get_process(
            'p3').get_output_resource_model('robot')
        self.assertIsNotNone(main_resource_to_clear.refresh())
        self.assertIsNotNone(sub_resource_to_keep.refresh())
        self.assertIsNotNone(sub_resource_to_clear.refresh())

        ProtocolService.reset_process_of_protocol_id(
            sub_protocol.get_model().id, 'p2')

        # check that all the next processes of p2 are reset
        main_protocol = main_protocol.refresh()
        self.assertTrue(main_protocol.get_model().is_partially_run)
        self.assertTrue(main_protocol.get_process('p0').get_model().is_success)
        self.assertTrue(main_protocol.get_process('p5').get_model().is_draft)

        sub_protocol = sub_protocol.refresh()
        self.assertTrue(sub_protocol.get_model().is_partially_run)
        self.assertTrue(sub_protocol.get_process('p1').get_model().is_success)
        self.assertTrue(sub_protocol.get_process('p2').get_model().is_draft)
        self.assertTrue(sub_protocol.get_process(
            'p_wait').get_model().is_draft)
        self.assertTrue(sub_protocol.get_process('p3').get_model().is_draft)
        self.assertTrue(sub_protocol.get_process('p4').get_model().is_draft)

        # Check that the resource of resetted process is deleted and the other are kept
        self.assertIsNone(ResourceModel.get_by_id(main_resource_to_clear.id))
        self.assertIsNotNone(ResourceModel.get_by_id(sub_resource_to_keep.id))
        self.assertIsNone(ResourceModel.get_by_id(sub_resource_to_clear.id))

        # rerun the experiment and check that it is successfull
        experiment.refresh()
        experiment.run()
        self.assertTrue(experiment.get_experiment_model().is_success)
        main_protocol = experiment.get_protocol()
        self.assertTrue(main_protocol.get_model().is_success)

        # Test using the output resource in another experiment and the first process should not be resettable
        # retrieve the main resource
        main_resource: ResourceModel = main_protocol.get_process(
            'p5').get_output_resource_model('robot')

        experiment2 = IExperiment()
        robot_mode = experiment2.get_protocol().add_task(RobotMove, 'robot')
        experiment2.get_protocol().add_source(
            'source', main_resource.id, robot_mode << 'robot')

        with self.assertRaises(ResourceUsedInAnotherExperimentException):
            ProtocolService.reset_process_of_protocol_id(
                sub_protocol.get_model().id, 'p2')

    def test_dynamic_ports(self):
        """ Test add dynamic input and output ports to a process.
        Test update the type of a dynamic port.
        Test delete a dynamic port.
        """
        protocol: ProtocolModel = ExperimentService.create_experiment().protocol_model
        # add a process with a dynamic port
        process_model: ProcessModel = ProtocolService.add_process_to_protocol(protocol, PyLiveTask, 'p1').process

        # Check that it has 1 input and 1 output
        self.assertEqual(len(process_model.inputs.ports.values()), 1)
        self.assertEqual(len(process_model.outputs.ports.values()), 1)

        # Add a dynamic port to the process
        process_model = ProtocolService.add_dynamic_input_port_to_process(protocol.id,
                                                                          process_model.instance_name).process

        # Check that it has 2 inputs
        self.assertEqual(len(process_model.inputs.ports.values()), 2)

        port_name = list(process_model.inputs.ports.keys())[1]
        # check the created port
        port = process_model.inputs.get_port(port_name)
        self.assertEqual(port.resource_spec.get_default_resource_type(), Resource)

        # Update new port type
        typing = Typing.get_by_model_type(Robot)
        io_spec: IOSpecDict = {
            'resource_types': [{
                'human_name': 'Robot',
                'typing_name': typing.typing_name,
                'brick_version': typing.brick_version
            }]
        }
        process_model = ProtocolService.update_dynamic_input_port_of_process(protocol.id,
                                                                             process_model.instance_name,
                                                                             port_name,
                                                                             io_spec).process

        # Check that the port type was updated
        port = process_model.inputs.get_port(port_name)
        self.assertEqual(port.resource_spec.get_default_resource_type(), Robot)

        # connect source to the new port
        # add a source to the input
        resource_model: ResourceModel = ResourceModel.save_from_resource(Robot.empty(), ResourceOrigin.UPLOADED)
        source_model: ProcessModel = ProtocolService.add_source_to_process_input(
            protocol.id, resource_model.id, process_model.instance_name, port_name).process

        protocol = protocol.refresh()
        self.assertEqual(len(protocol.connectors), 1)

        # Delete port and check that the connector was deleted
        process_model = ProtocolService.delete_dynamic_input_port_of_process(
            protocol.id, process_model.instance_name, port_name).process

        self.assertEqual(len(process_model.inputs.ports.values()), 1)
        protocol = protocol.refresh()
        self.assertEqual(len(protocol.connectors), 0)

        # Add a dynamic output port to the process
        process_model = ProtocolService.add_dynamic_output_port_to_process(protocol.id,
                                                                           process_model.instance_name).process

        # Check that it has 2 outputs
        self.assertEqual(len(process_model.outputs.ports.values()), 2)

        port_name = list(process_model.outputs.ports.keys())[1]

        # Delete the output port
        process_model = ProtocolService.delete_dynamic_output_port_of_process(protocol.id, process_model.instance_name,
                                                                              port_name).process
        process_model = process_model.refresh()
        protocol = protocol.refresh()

    def test_run_protocol_process(self):
        experiment = IExperiment(TestSimpleProtocol)

        # Run process p0
        ProtocolService.run_process(experiment.get_protocol().get_model().id, 'p0')
        experiment.refresh()
        self.assertTrue(experiment.get_protocol().get_process('p0').get_model().is_success)
        self.assertTrue(experiment.get_protocol().get_process('p1').get_model().is_draft)

        # Test run process p1
        ProtocolService.run_process(experiment.get_protocol().get_model().id, 'p1')
        experiment.refresh()
        self.assertTrue(experiment.get_protocol().get_process('p1').get_model().is_success)

        # Test ru nprocess p4 which shoud not be runable
        with self.assertRaises(Exception):
            ProtocolService.run_process(experiment.get_protocol().get_model().id, 'p4')
