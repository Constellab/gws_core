# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (ConfigParams, DynamicInputs, DynamicOutputs, InputSpec,
                      OutputSpec, ResourceModel, Table, Task, TaskInputs,
                      TaskOutputs, task_decorator)
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.impl.robot.robot_resource import Robot
from gws_core.io.io_spec import IOSpecDTO
from gws_core.model.typing import Typing
from gws_core.model.typing_dict import TypingRefDTO
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.resource.resource import Resource
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.test.base_test_case import BaseTestCase


@task_decorator("TestDynamicIO")
class TestDynamicIO(Task):

    input_specs = DynamicInputs({
        'table': InputSpec(Table),
    }, additionnal_port_spec=InputSpec(Table))

    output_specs = DynamicOutputs({
        'resource': OutputSpec(Resource),
    }, additionnal_port_spec=OutputSpec(Resource))


def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
    return {'target': inputs['source']}


# test_dynamic_ports
class TestDynamicPorts(BaseTestCase):

    def test_dynamic_ports(self):
        """ Test add dynamic input and output ports to a process.
        Test update the type of a dynamic port.
        Test delete a dynamic port.
        """
        protocol: ProtocolModel = ExperimentService.create_experiment().protocol_model
        # add a process with a dynamic port
        process_model: ProcessModel = ProtocolService.add_process_to_protocol(protocol, TestDynamicIO, 'p1').process

        # Check that it has 1 input and 1 output
        self.assertEqual(len(process_model.inputs.ports.values()), 1)
        self.assertEqual(len(process_model.outputs.ports.values()), 1)

        # Add a dynamic port to the process
        process_model = ProtocolService.add_dynamic_input_port_to_process(protocol.id,
                                                                          process_model.instance_name).process

        # Check that it has 2 inputs
        self.assertEqual(len(process_model.inputs.ports.values()), 2)

        # Check that the port type is Table
        for port in process_model.inputs.ports.values():
            self.assertEqual(port.resource_spec.get_default_resource_type(), Table)

        port_name = list(process_model.inputs.ports.keys())[1]

        # Update new port type
        typing = Typing.get_by_model_type(Robot)
        io_spec = IOSpecDTO(
            resource_types=[
                TypingRefDTO(
                    human_name='Robot',
                    typing_name=typing.typing_name,
                    brick_version=typing.brick_version
                )
            ],
            is_optional=False,
        )
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
        ProtocolService.add_source_to_process_input(
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
        # Check that the port type is Resource
        for port in process_model.outputs.ports.values():
            self.assertEqual(port.resource_spec.get_default_resource_type(), Resource)

        port_name = list(process_model.outputs.ports.keys())[1]

        # Delete the output port
        process_model = ProtocolService.delete_dynamic_output_port_of_process(protocol.id, process_model.instance_name,
                                                                              port_name).process
        process_model = process_model.refresh()
        protocol = protocol.refresh()
