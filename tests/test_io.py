# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional, Union

from gws_core import (BaseTestCase, ConfigParams, Connector, GTest, Process,
                      ProcessableFactory, ProcessInputs, ProcessModel,
                      ProcessOutputs, Resource, SerializedResourceData,
                      process_decorator, resource_decorator)
from gws_core.io.io_exception import ImcompatiblePortsException
from gws_core.io.io_spec import SubClasses


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
    output_specs = {'jump_person_out': Person,
                    'jump_person_out_any': SubClasses[Person]}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        return


@process_decorator("Fly")
class Fly(Process):
    input_specs = {'superman': SuperMan}
    output_specs = {}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        return


@process_decorator("OptionalProcess")
class OptionalProcess(Process):
    input_specs = {'first': Optional[Person],
                   'second': Union[Person, None],
                   'third': Person}
    output_specs = {}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        return


class TestIO(BaseTestCase):

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

        with self.assertRaises(ImcompatiblePortsException):
            Connector(p2.out_port('move_person_out'), p3.in_port('move_drive_in'))

        self.assertEqual(port_connect.to_json(), {
            "from": {"node": "p0",  "port": "create_person_out"},
            "to": {"node": "p1",  "port": "move_person_in"},
            'resource': {'uri': '', 'typing_name': ''}
        })

    def test_optional(self):
        opt: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=OptionalProcess, instance_name="optional")

        self.assertTrue(opt.in_port("first").is_optional)
        self.assertTrue(opt.in_port("second").is_optional)
        self.assertFalse(opt.in_port("third").is_optional)

    def test_sub_class(self):
        """Test the SubClasses generic type
        """
        jump: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=Jump, instance_name="jump")
        fly: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=Fly, instance_name="fly")

        # Test that you can't plug a Person to a Superman
        with self.assertRaises(Exception):
            Connector(jump.out_port('jump_person_out'), fly.in_port('superman'))

        # Test that you can plus a SubClasses[Person] to a Superman
        Connector(jump.out_port('jump_person_out_any'), fly.in_port('superman'))
