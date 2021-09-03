# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, Connector, GTest, Process,
                      ProcessableFactory, process_decorator, ProcessInputs,
                      ProcessModel, ProcessOutputs, Resource,
                      resource_decorator, SerializedResourceData)

from tests.base_test import BaseTest


@resource_decorator("Person")
class Person(Resource):
    def serialize_data(self) -> SerializedResourceData:
        return {}

    def deserialize_data(self, data: SerializedResourceData) -> None:
        pass


@resource_decorator("Man")
class Man(Person):
    pass


@resource_decorator("SuperMan")
class SuperMan(Man):
    pass


@resource_decorator("Car")
class Car(Resource):
    def serialize_data(self) -> SerializedResourceData:
        return {}

    def deserialize_data(self, data: SerializedResourceData) -> None:
        pass


@process_decorator("Create")
class Create(Process):
    input_specs = {}
    output_specs = {'create_person_out': Person}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        return


@process_decorator("Move")
class Move(Process):
    input_specs = {'move_person_in': Person}
    output_specs = {'move_person_out': Person}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        return


@process_decorator("Drive")
class Drive(Process):
    input_specs = {'move_drive_in': Car}
    output_specs = {'move_drive_out': Car}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        return


@process_decorator("Jump")
class Jump(Process):
    input_specs = {'jump_person_in_1': Person,
                   'jump_person_in_2': Person}
    output_specs = {'jump_person_out': Person}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        return


class TestIO(BaseTest):

    def test_connect(self):
        GTest.print("IO connect")

        p0: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=Create, instance_name="p0")
        p1: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=Move, instance_name="p1")
        p2: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=Move, instance_name="p2")

        # create a chain
        port_connect: Connector = Connector(p0.out_port('create_person_out'), p1.in_port('move_person_in'))

        out_port = p0.out_port('create_person_out')
        self.assertEqual(out_port.name, 'create_person_out')

        in_port = p1.in_port('move_person_in')
        self.assertEqual(in_port.name, 'move_person_in')

        self.assertIsInstance(port_connect, Connector)

        # assert error
        p3: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=Drive, instance_name="p3")

        with self.assertRaises(Exception):
            Connector(p2.out_port['move_person_out'], p3.in_port('move_drive_in'))

        self.assertEqual(port_connect.to_json(), {
            "from": {"node": "p0",  "port": "create_person_out"},
            "to": {"node": "p1",  "port": "move_person_in"},
            'resource': {'uri': '', 'typing_name': ''}
        })

    def test_iterator(self):
        GTest.print("IO Iterator")

        jump: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=Jump, instance_name="p3")
        for k in jump.input:
            print(k)
            print(jump.input.get_resource_model(k))
