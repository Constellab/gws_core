

import os

from pandas import DataFrame

from gws_core import (ConfigParams, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, Resource, Task, TaskInputs, TaskOutputs,
                      resource_decorator, task_decorator)
from gws_core.core.utils.compress.zip_compress import ZipCompress
from gws_core.core.utils.settings import Settings
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate
from gws_core.impl.table.table import Table
from gws_core.io.dynamic_io import DynamicInputs
from gws_core.protocol.protocol_interface import IProtocol
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_set.resource_set import ResourceSet
from gws_core.resource.resource_set.resource_set_exporter import \
    ResourceSetExporter
from gws_core.resource.resource_set.resource_set_tasks import ResourceStacker
from gws_core.task.task_runner import TaskRunner
from gws_core.test.base_test_case import BaseTestCase


@resource_decorator(unique_name="EmptyResource")
class EmptyResource(Resource):
    pass


@task_decorator(unique_name="RobotsGenerator")
class RobotsGenerator(Task):

    input_specs: InputSpecs = InputSpecs({"robot_i": InputSpec(Robot)})
    output_specs: OutputSpecs = OutputSpecs({'set': OutputSpec(ResourceSet)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        robot_1 = inputs.get('robot_i')
        robot_2 = Robot.empty()
        robot_2.age = 99
        robot_2.name = "Robot 2"

        resource_set: ResourceSet = ResourceSet()
        # Add the input robot that was already created and saved
        resource_set.add_resource(
            robot_1, unique_name="Robot 1", create_new_resource=False)
        resource_set.add_resource(robot_2)
        return {'set': resource_set}


@task_decorator(unique_name="RobotsAdd")
class RobotsAdd(Task):

    input_specs: InputSpecs = InputSpecs({"set": InputSpec(ResourceSet)})
    output_specs: OutputSpecs = OutputSpecs({'set': OutputSpec(ResourceSet)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # this task takes the resource set and add a new robot
        # keeps the resources that where already in the set
        resource_set: ResourceSet = inputs.get('set')
        robot_3 = Robot.empty()
        robot_3.age = 100
        robot_3.name = "Robot 3"
        resource_set.add_resource(robot_3)

        return {'set': resource_set}


# test_resource_set
class TestResourceSet(BaseTestCase):

    def test_resource_set(self):

        resource_count = ResourceModel.select().count()
        experiment: IExperiment = IExperiment()
        protocol: IProtocol = experiment.get_protocol()
        robot_create = experiment.get_protocol().add_process(RobotCreate, 'create')
        robot_generator = protocol.add_process(RobotsGenerator, 'generator')
        robot_add = protocol.add_process(RobotsAdd, 'add')
        experiment.get_protocol().add_connectors([
            (robot_create >> 'robot', robot_generator << 'robot_i'),
            (robot_generator >> 'set', robot_add << 'set')
        ])

        experiment.run()

        robot_generator.refresh()
        robot_create.refresh()
        robot_add.refresh()

        # check that it created 5 resources (2 for the resource set and 3 robots)
        self.assertEqual(ResourceModel.select().count(), resource_count + 5)

        resource_set: ResourceSet = robot_generator.get_output('set')

        self.assertEqual(len(resource_set.get_resources()), 2)

        age = 0
        for resource in resource_set.get_resources().values():
            self.assertIsInstance(resource, Robot)
            age += resource.age

        # check the age, this will mean the two where correctly saved separatly
        self.assertEqual(age, 9 + 99)

        # Test get_resource
        robot_1: Robot = resource_set.get_resource('Robot 1')
        self.assertEqual(robot_1.age, 9)

        # Test get_resource
        robot_2 = resource_set.get_resource('Robot 2')
        self.assertEqual(robot_2.name, 'Robot 2')

        # test the view, reload the resource to simulate real view
        resource_set = ResourceModel.get_by_id_and_check(
            resource_set._model_id).get_resource()

        self.assertEqual(
            len(resource_set.view_resources_list({}).to_dto({}).data), 2)

        # check that output or robot add has 3 robots
        resource_set = robot_add.get_output('set')
        self.assertEqual(len(resource_set.get_resources()), 3)
        self.assertTrue(resource_set.resource_exists('Robot 2'))
        self.assertTrue(resource_set.resource_exists('Robot 3'))

        # check that the reset cleared the correct resources
        experiment.get_model().reset()
        self.assertEqual(ResourceModel.select().count(), resource_count)

    def test_resource_set_exporter(self):
        settings = Settings.get_instance()

        # exportable resource
        table = Table(DataFrame({'a': [1, 2, 3]}))
        # resource not exportable
        empty_resource = EmptyResource()

        # add a file
        file_path = FileHelper.create_empty_file_if_not_exist(
            os.path.join(settings.make_temp_dir(), 'test.json'))
        file = File(file_path)

        resource_set: ResourceSet = ResourceSet()
        resource_set.add_resource(table, unique_name='table')
        resource_set.add_resource(empty_resource, unique_name='empty_resource')
        resource_set.add_resource(file, unique_name='test')

        zip_file: File = ResourceSetExporter.call(resource_set, {})

        self.assertTrue(zip_file.exists())

        dest_folder = settings.make_temp_dir()
        ZipCompress.decompress(zip_file.path, dest_folder)

        self.assertTrue(os.path.exists(os.path.join(dest_folder, 'table.csv')))
        self.assertTrue(os.path.exists(os.path.join(dest_folder, 'test.json')))
        # empty resource should not be exported
        self.assertFalse(os.path.exists(
            os.path.join(dest_folder, 'empty_resource.json')))

    def test_resource_stacker(self):
        robot_1 = Robot.empty()
        ResourceModel.save_from_resource(robot_1, ResourceOrigin.UPLOADED)
        robot_2 = Robot.empty()
        robot_2.name = 'robot_2'
        ResourceModel.save_from_resource(robot_2, ResourceOrigin.UPLOADED)

        robot_3 = Robot.empty()
        robot_3.name = 'robot_3'
        ResourceModel.save_from_resource(robot_3, ResourceOrigin.UPLOADED)
        resource_set: ResourceSet = ResourceSet()
        resource_set.add_resource(robot_3, create_new_resource=False)
        ResourceModel.save_from_resource(resource_set, ResourceOrigin.UPLOADED)

        task_runner = TaskRunner(ResourceStacker,
                                 params={'keys': [
                                        {'key': 'robot_1'},
                                        {'key': ''},
                                        {'key': 'robot_3'},
                                        {'key': 'resource_set'}
                                 ]},
                                 inputs={'resource_1': robot_1,
                                         'resource_2': robot_2,
                                         'resource_3': None,
                                         'resource_4': resource_set},
                                 input_specs=DynamicInputs({
                                     'resource_1': InputSpec(Robot),
                                     'resource_2': InputSpec(Robot),
                                     'resource_3': InputSpec(Robot, is_optional=True),
                                     'resource_4': InputSpec(ResourceSet)
                                 })
                                 )

        outputs = task_runner.run()

        resource_set: ResourceSet = outputs.get('resource_set')

        self.assertIsInstance(resource_set, ResourceSet)
        self.assertEqual(len(resource_set.get_resources()), 3)
        self.assertEqual(resource_set.get_resource('robot_1').uid, robot_1.uid)
        self.assertEqual(resource_set.get_resource('robot_2').uid, robot_2.uid)
        # check that the sub resource set was flatten
        self.assertEqual(resource_set.get_resource('robot_3').uid, robot_3.uid)
