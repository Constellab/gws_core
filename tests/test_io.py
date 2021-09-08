# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, ConfigParams, Connector, GTest, Process,
                      ProcessableFactory, ProcessInputs, ProcessModel,
                      ProcessOutputs, Resource, SerializedResourceData,
                      process_decorator, resource_decorator)
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.io.io_exception import ImcompatiblePortsException
from gws_core.io.io_types import OptionalIn, SpecialTypeOut, UnmodifiedOut
from gws_core.process.plug import FIFO2, Wait
from gws_core.protocol.protocol import Protocol
from gws_core.protocol.protocol_decorator import protocol_decorator
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.protocol.protocol_spec import ProcessableSpec
from gws_core.resource.resource_model import ResourceModel


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
        return {'create_person_out': Person()}


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
                    'jump_person_out_any': SpecialTypeOut(resource_types=Person, sub_class=True)}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        return


@process_decorator("Multi")
class Multi(Process):
    input_specs = {'resource_1': (Car, Person),
                   'resource_2': [Car, Person]}
    output_specs = {'resource_1': (Car, Person),
                    'resource_2': [Car, Person]}
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
    input_specs = {'first': OptionalIn([Person]),
                   'second': [Person, None],
                   'third': Person}
    output_specs = {}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        return

# Use to check that 2 optional process can"t plug if types are not correct (even if both have None)


@process_decorator("OptionalProcessOut")
class OptionalProcessOut(Process):
    input_specs = {}
    output_specs = {'out': OptionalIn(Car)}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        return


# This is to test the UnmodifiedOut type
@process_decorator("Log")
class Log(Process):
    input_specs = {'person': Person}
    output_specs = {'samePerson': UnmodifiedOut(Person),
                    'otherPerson': Person}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        print('Log person')
        return {'samePerson': inputs.get('person'), 'otherPerson': inputs.get('person')}


@protocol_decorator("TestPersonProtocol")
class TestPersonProtocol(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        create: ProcessableSpec = self.add_process(Create, 'create')
        log: ProcessableSpec = self.add_process(Log, 'log')

        self.add_connectors([
            (create >> 'create_person_out', log << 'person')
        ])


@process_decorator(unique_name="FIFO2")
class Skippable(FIFO2):
    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:

        resource1 = inputs.get("resource_1")
        resource2 = inputs.get("resource_2")

        if resource1 and resource2:
            raise BadRequestException('The two resources are set and it should be only one because of Skippable')

        return await super().task(config=config, inputs=inputs)


@protocol_decorator("TestSkippable")
class TestSkippable(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        create1: ProcessableSpec = self.add_process(Create, 'create1')
        wait: ProcessableSpec = self.add_process(Wait, 'wait').configure('waiting_time', '3')
        create2: ProcessableSpec = self.add_process(Create, 'create2')
        skippable: ProcessableSpec = self.add_process(Skippable, 'skippable')
        move: ProcessableSpec = self.add_process(Move, 'move')

        self.add_connectors([
            (create1 >> 'create_person_out', wait << 'resource'),
            (wait >> 'resource', skippable << 'resource_1'),
            (create2 >> 'create_person_out', skippable << 'resource_2'),
            (skippable >> 'resource', move << 'move_person_in'),
        ])


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

    def test_multi(self):
        """Test inputs and output with multi types
        """
        create: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=Create, instance_name="create")
        multi: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=Multi, instance_name="multi")
        jump: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=Jump, instance_name="move")

        # Test that you can plug create to multi move_person_in
        Connector(create.out_port('create_person_out'), multi.in_port('resource_1'))
        Connector(create.out_port('create_person_out'), multi.in_port('resource_2'))

        # Test that you can plug multi to moves
        Connector(multi.out_port('resource_1'), jump.in_port('jump_person_in_1'))
        Connector(multi.out_port('resource_2'), jump.in_port('jump_person_in_2'))

    def test_optional(self):
        """Test optional option and provide None to an optional object
        """
        opt: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=OptionalProcess, instance_name="optional")

        self.assertTrue(opt.in_port("first").is_optional)
        self.assertTrue(opt.in_port("second").is_optional)
        self.assertFalse(opt.in_port("third").is_optional)

        opt_car: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=OptionalProcessOut, instance_name="optional2")

        with self.assertRaises(ImcompatiblePortsException):
            Connector(opt_car.out_port('out'), opt.in_port('first'))

    def test_sub_class_output(self):
        """Test the SubClasses option on output special type
        """
        jump: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=Jump, instance_name="jump")
        fly: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=Fly, instance_name="fly")

        # Test that you can't plug a Person to a Superman
        with self.assertRaises(Exception):
            Connector(jump.out_port('jump_person_out'), fly.in_port('superman'))

        # Test that you can plug a subclass of Person to a Superman
        Connector(jump.out_port('jump_person_out_any'), fly.in_port('superman'))

    async def test_unmodified_output(self):
        """Test the UnmodifiableOut type. It tests that this is the same resource
        on log input and log output
        """
        protocol: ProtocolModel = ProcessableFactory.create_protocol_model_from_type(TestPersonProtocol)
        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(protocol)

        experiment = await ExperimentService.run_experiment(experiment)

        person1: ResourceModel = experiment.protocol.get_process('create').out_port('create_person_out').resource_model
        same_person: ResourceModel = experiment.protocol.get_process('log').out_port('samePerson').resource_model
        other_erson: ResourceModel = experiment.protocol.get_process('log').out_port('otherPerson').resource_model

        self.assertEqual(person1.id, same_person.id)
        self.assertNotEqual(person1, other_erson.id)

    async def test_skippable_input(self):
        """Test the SkippableIn special type with FIFO, it also tests that FIFO work
        (testing,SkippableIn but also UnmodifiableOut with subclass) """
        protocol: ProtocolModel = ProcessableFactory.create_protocol_model_from_type(TestSkippable)
        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(protocol)

        experiment = await ExperimentService.run_experiment(experiment)

        create2: ProcessModel = experiment.protocol.get_process('create2')
        skippable: ProcessModel = experiment.protocol.get_process('skippable')

        create_2_r: ResourceModel = create2.out_port('create_person_out').resource_model
        skippable_r: ResourceModel = skippable.out_port('resource').resource_model
        # Check that this is the create_2 that passed through skippable process
        self.assertEqual(create_2_r.id, skippable_r.id)
