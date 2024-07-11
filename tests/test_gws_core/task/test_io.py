

from gws_core import (BadRequestException, BaseTestCase, ConfigParams,
                      Connector, Experiment, ExperimentService, InputSpecs,
                      OutputSpecs, ProcessFactory, ProcessSpec, Protocol,
                      ProtocolModel, Resource, ResourceModel, Task, TaskInputs,
                      TaskModel, TaskOutputs, protocol_decorator,
                      resource_decorator, task_decorator)
from gws_core.experiment.experiment_run_service import ExperimentRunService
from gws_core.io.io_exception import ImcompatiblePortsException
from gws_core.io.io_spec import InputSpec, OutputSpec


@resource_decorator("Person")
class Person(Resource):
    pass


@resource_decorator("Man")
class Man(Person):
    pass


@resource_decorator("SuperMan")
class SuperMan(Man):
    pass


@resource_decorator("Car")
class Car(Resource):
    pass


@task_decorator("Create")
class Create(Task):
    output_specs = OutputSpecs({'create_person_out': OutputSpec(Person)})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {'create_person_out': Person()}


@task_decorator("Move")
class Move(Task):
    input_specs = InputSpecs({'move_person_in': InputSpec(Person)})
    output_specs = OutputSpecs({'move_person_out': OutputSpec(Person)})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {'move_person_out': inputs['move_person_in']}


@task_decorator("Drive")
class Drive(Task):
    input_specs = InputSpecs({'move_drive_in': InputSpec(Car)})
    output_specs = OutputSpecs({'move_drive_out': OutputSpec(Car)})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {'move_drive_out': inputs['move_drive_in']}


@task_decorator("Jump")
class Jump(Task):
    input_specs = InputSpecs({'jump_person_in_1': InputSpec(Person),
                              'jump_person_in_2': InputSpec(Person)})
    output_specs = OutputSpecs({'jump_person_out': OutputSpec(Person),
                                'jump_person_out_any': OutputSpec(resource_types=Person, sub_class=True)})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {'jump_person_out': inputs['jump_person_in_1'], 'jump_person_out_any': inputs['jump_person_in_2']}


@task_decorator("Multi")
class Multi(Task):
    input_specs = InputSpecs({'resource_1': InputSpec((Car, Person)),
                              'resource_2': InputSpec([Car, Person])})
    output_specs = OutputSpecs({'resource_1': OutputSpec((Car, Person)),
                                'resource_2': OutputSpec([Car, Person])})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {'resource_1': inputs['resource_1'], 'resource_2': inputs['resource_2']}


@task_decorator("Fly")
class Fly(Task):
    input_specs = InputSpecs({'superman': InputSpec(SuperMan)})
    output_specs = OutputSpecs({})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {}


@task_decorator("OptionalTask")
class OptionalTask(Task):
    input_specs = InputSpecs({'first': InputSpec([Person], is_optional=True),
                              'second': InputSpec(Person, is_optional=True),
                              'third': InputSpec(Person)})
    output_specs = OutputSpecs({})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {}

# Use to check that 2 optional task can"t plug if types are not correct (even if both have None)


@task_decorator("OptionalTaskOut")
class OptionalTaskOut(Task):
    output_specs = OutputSpecs({'out': OutputSpec(Car)})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {}


# This is to test the ConstantOut type
@task_decorator("Log")
class Log(Task):
    input_specs = InputSpecs({'person': InputSpec(Person)})
    output_specs = OutputSpecs({'samePerson': OutputSpec(Person, is_constant=True),
                                'otherPerson': OutputSpec(Person)})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {'samePerson': inputs.get('person'), 'otherPerson': inputs.get('person')}


@protocol_decorator("TestPersonProtocol")
class TestPersonProtocol(Protocol):
    def configure_protocol(self) -> None:
        create: ProcessSpec = self.add_process(Create, 'create')
        log: ProcessSpec = self.add_process(Log, 'log')

        self.add_connectors([
            (create >> 'create_person_out', log << 'person')
        ])


@task_decorator(unique_name="FIFO2")
class Skippable(Task):

    input_specs: InputSpecs = InputSpecs({'resource_1': InputSpec(Resource, is_optional=True),
                                          'resource_2': InputSpec(Resource, is_optional=True)})
    output_specs: OutputSpecs = OutputSpecs({'resource': OutputSpec(
        resource_types=Resource, sub_class=True, is_constant=True)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        resource1 = inputs.get("resource_1")
        resource2 = inputs.get("resource_2")

        if resource1 and resource2:
            raise BadRequestException(
                'The two resources are set and it should be only one because of Skippable')

        return super().run(params, inputs)


@protocol_decorator("TestSkippable")
class TestSkippable(Protocol):
    def configure_protocol(self) -> None:
        create1: ProcessSpec = self.add_process(Create, 'create1')
        create2: ProcessSpec = self.add_process(Create, 'create2')
        skippable: ProcessSpec = self.add_process(Skippable, 'skippable')
        move: ProcessSpec = self.add_process(Move, 'move')

        self.add_connectors([
            (create1 >> 'create_person_out', skippable << 'resource_1'),
            (create2 >> 'create_person_out', skippable << 'resource_2'),
            (skippable >> 'resource', move << 'move_person_in'),
        ])


# test_io
class TestIO(BaseTestCase):

    def test_connect(self):

        process_0: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=Create, instance_name="p0")
        process_1: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=Move, instance_name="p1")
        process_2: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=Move, instance_name="p2")

        # create a chain
        port_connect: Connector = Connector(
            process_0, process_1, 'create_person_out', 'move_person_in')

        out_port = process_0.out_port('create_person_out')
        self.assertEqual(out_port.name, 'create_person_out')

        in_port = process_1.in_port('move_person_in')
        self.assertEqual(in_port.name, 'move_person_in')

        self.assertIsInstance(port_connect, Connector)

        # assert error
        process_3: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=Drive, instance_name="p3")

        with self.assertRaises(ImcompatiblePortsException):
            Connector(process_2, process_3, 'move_person_out',
                      'move_drive_in')

        self.assertEqual(port_connect.to_dto().to_json_dict(), {
            "from": {"node": "p0",  "port": "create_person_out"},
            "to": {"node": "p1",  "port": "move_person_in"},
        })

    def test_multi(self):
        """Test inputs and output with multi types
        """
        create: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=Create, instance_name="create")
        multi: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=Multi, instance_name="multi")
        jump: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=Jump, instance_name="move")

        # Test that you can plug create to multi move_person_in
        Connector(create, multi, 'create_person_out',
                  'resource_1')
        Connector(create, multi, 'create_person_out',
                  'resource_2')

        # Test that you can plug multi to moves
        Connector(multi, jump, 'resource_1',
                  'jump_person_in_1')
        Connector(multi, jump, 'resource_2',
                  'jump_person_in_2')

    def test_optional(self):
        """Test optional option and provide None to an optional object
        """
        opt: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=OptionalTask, instance_name="optional")

        self.assertTrue(opt.in_port("first").is_optional)
        self.assertTrue(opt.in_port("second").is_optional)
        self.assertFalse(opt.in_port("third").is_optional)

        opt_car: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=OptionalTaskOut, instance_name="optional2")

        with self.assertRaises(ImcompatiblePortsException):
            Connector(opt_car, opt, 'out', 'first')

    def test_sub_class_output(self):
        """Test the SubClasses option on output special type
        """
        jump: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=Jump, instance_name="jump")
        fly: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=Fly, instance_name="fly")

        # Test that you can't plug a Person to a Superman
        with self.assertRaises(Exception):
            Connector(jump, fly, 'jump_person_out',
                      'superman')

        # Test that you can plug a subclass of Person to a Superman
        Connector(jump, fly, 'jump_person_out_any',
                  'superman')

    def test_unmodified_output(self):
        """Test the UnmodifiableOut type. It tests that this is the same resource
        on log input and log output
        """
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_type(
            TestPersonProtocol)
        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol)

        experiment = ExperimentRunService.run_experiment(experiment)

        person1: ResourceModel = experiment.protocol_model.get_process(
            'create').out_port('create_person_out').get_resource_model()
        same_person: ResourceModel = experiment.protocol_model.get_process(
            'log').out_port('samePerson').get_resource_model()
        other_erson: ResourceModel = experiment.protocol_model.get_process(
            'log').out_port('otherPerson').get_resource_model()

        self.assertEqual(person1.id, same_person.id)
        self.assertNotEqual(person1, other_erson.id)
