

from datetime import timedelta

from gws_core import (ConfigParams, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, Task, TaskInputs, TaskOutputs,
                      task_decorator)
from gws_core.core.utils.date_helper import DateHelper
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotMove
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_set.resource_set import ResourceSet
from gws_core.scenario.scenario_enums import ScenarioCreationType
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.task.scenario_downloader import ScenarioDownloader
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.shared_dto import GenerateShareLinkDTO, ShareLinkType
from gws_core.share.shared_resource import SharedResource
from gws_core.share.shared_scenario import SharedScenario
from gws_core.task.plug import Sink, Source
from gws_core.task.task_input_model import TaskInputModel
from gws_core.task.task_model import TaskModel
from gws_core.task.task_runner import TaskRunner
from gws_core.test.base_test_case import BaseTestCase
from gws_core.test.gtest import GTest, TestStartUvicornApp


@task_decorator(unique_name="RobotsGeneratorShare")
class RobotsGeneratorShare(Task):

    input_specs: InputSpecs = InputSpecs({"robot": InputSpec(Robot)})
    output_specs: OutputSpecs = OutputSpecs({'set': OutputSpec(ResourceSet)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        robot_1 = inputs.get('robot')
        robot_2 = Robot.empty()
        robot_2.age = 99
        robot_2.name = "Robot 2"

        resource_set: ResourceSet = ResourceSet()
        # Add the input robot that was already created and saved
        resource_set.add_resource(
            robot_1, unique_name="Robot 1", create_new_resource=False)
        resource_set.add_resource(robot_2)
        return {'set': resource_set}


# test_share_scenario
class TestShareScenario(BaseTestCase):

    def test_share_scenario(self):
        # activate uvicorn, so the ScenarioDownloader can request the API
        with TestStartUvicornApp():

            input_robot_model = GTest.save_robot_resource()

            # Create and run an scenario
            folder = GTest.create_default_folder()
            scenario = ScenarioProxy(title='Test scenario', folder=folder)
            protocol = scenario.get_protocol()

            move = protocol.add_process(RobotMove, 'move', config_params={'moving_step': 100})
            generate = protocol.add_process(RobotsGeneratorShare, 'generate')

            # Source > Move > RobotsGenerator > Sink
            source = protocol.add_source('source', input_robot_model.id, move << 'robot')
            protocol.add_connector(move >> 'robot', generate << 'robot')
            sink = protocol.add_sink('sink', generate >> 'set')
            scenario.run()

            initial_scenario_model = scenario.refresh().get_model()
            initial_protocol_model: ProtocolModel = protocol.refresh().get_model()
            source_process_model = source.refresh().get_model()
            move_process_model = move.refresh().get_model()
            generate_process_model = generate.refresh().get_model()
            sink_process_model = sink.refresh().get_model()

            # generate share link
            share_dto = GenerateShareLinkDTO(
                entity_id=scenario.get_model().id,
                entity_type=ShareLinkType.SCENARIO,
                valid_until=DateHelper.now_utc() + timedelta(days=1)
            )

            share_link = ShareLinkService.generate_share_link(share_dto)

            task_runner = TaskRunner(ScenarioDownloader, params={
                'link': share_link.get_link(),
                'resource_mode': 'All'
            })

            outputs = task_runner.run()

            scenario_resource: ScenarioResource = outputs['scenario']

            new_scenario = scenario_resource.get_scenario()

            self.assertEqual(new_scenario.title, initial_scenario_model.title)
            self.assertEqual(new_scenario.folder.id, folder.id)
            self.assertEqual(new_scenario.status, initial_scenario_model.status)
            self.assertEqual(new_scenario.creation_type, ScenarioCreationType.IMPORTED)

            new_protocol_model = new_scenario.protocol_model

            # Check the protocol
            self.assertEqual(len(new_protocol_model.processes), 4)
            self.assertEqual(len(new_protocol_model.connectors), 3)
            self.assertEqual(new_protocol_model.status, initial_protocol_model.status)
            self.assertEqual(new_protocol_model.progress_bar.get_elapsed_time(),
                             initial_protocol_model.progress_bar.get_elapsed_time())

            # check the processes
            new_source: TaskModel = new_protocol_model.get_process('source')
            self.assertEqual(new_source.process_typing_name, source_process_model.process_typing_name)

            new_move = new_protocol_model.get_process('move')
            self.assertEqual(new_move.process_typing_name, move_process_model.process_typing_name)
            self.assertEqual(new_move.status, move_process_model.status)
            self.assertEqual(new_move.progress_bar.get_elapsed_time(),
                             move_process_model.progress_bar.get_elapsed_time())

            self.assertEqual(new_protocol_model.get_process('generate').process_typing_name,
                             generate_process_model.process_typing_name)

            self.assertEqual(new_protocol_model.get_process('sink').process_typing_name,
                             sink_process_model.process_typing_name)

            # Check the source resource
            new_source_output = new_source.out_port(Source.output_name).get_resource_model()
            self.assertIsNotNone(new_source_output)
            self.assertEqual(new_source_output.origin, ResourceOrigin.IMPORTED_FROM_LAB)
            self.assertNotEqual(new_source_output.id, input_robot_model.id)
            self.assertTrue(new_source_output.flagged)
            # check that the source config id and the source config where update with the new resource id
            self.assertEqual(new_source.source_config_id, new_source_output.id)
            self.assertEqual(new_source.config.get_value(Source.config_name), new_source_output.id)

            # Check the resources
            new_move_process = new_protocol_model.get_process('move')
            # input resource has the same id as the output resource of the source
            self.assertEqual(new_move_process.in_port("robot").get_resource_model_id(), new_source_output.id)
            # output resource
            new_resource_1 = new_move_process.out_port("robot").get_resource_model()
            initial_resource_1 = initial_protocol_model.get_process('move').out_port("robot").get_resource_model()
            self.assertIsNotNone(new_resource_1)
            self.assertEqual(new_resource_1.origin, ResourceOrigin.GENERATED)
            self.assertEqual(new_resource_1.task_model.id, new_protocol_model.get_process('move').id)
            self.assertEqual(new_resource_1.scenario.id, new_scenario.id)
            self.assertEqual(new_resource_1.folder.id, new_scenario.folder.id)
            self.assertFalse(new_resource_1.flagged)
            self.assertNotEqual(new_resource_1.id, initial_resource_1.id)
            self.assertEqual(new_resource_1.resource_typing_name, initial_resource_1.resource_typing_name)

            # Check the resource set
            new_generator_process = new_protocol_model.get_process('generate')
            new_resource_set = new_generator_process.out_port("set").get_resource_model()
            self.assertIsNotNone(new_resource_set)
            self.assertTrue(new_resource_set.flagged)
            resource_set: ResourceSet = new_resource_set.get_resource()
            self.assertIsInstance(resource_set, ResourceSet)
            self.assertEqual(len(resource_set.get_resources()), 2)

            # Check that the task input model where created
            self.assertEqual(TaskInputModel.get_by_scenario(new_scenario.id).count(), 3)

            # Check taht the ShareScenario was created
            self.assertIsNotNone(SharedScenario.get_and_check_entity_origin(new_scenario.id))
            self.assertIsNotNone(SharedResource.get_and_check_entity_origin(new_source_output.id))

            ######################  Re-run the share without all resources ######################
            task_runner = TaskRunner(ScenarioDownloader, params={
                'link': share_link.get_link(),
                'resource_mode': 'Outputs only'
            })

            outputs = task_runner.run()

            scenario_resource_2: ScenarioResource = outputs['scenario']
            new_scenario_2 = scenario_resource_2.get_scenario()
            new_protocol_2 = new_scenario_2.protocol_model
            # Check that the task input model where created
            self.assertNotEqual(new_scenario_2.id, new_scenario.id)
            self.assertEqual(TaskInputModel.get_by_scenario(new_scenario_2.id).count(), 1)

            # the source task should not be configured as only the output resources are imported
            new_source_2: TaskModel = new_protocol_2.get_process('source')
            self.assertIsNone(new_source_2.source_config_id)
            self.assertIsNone(new_source_2.out_port(Source.output_name).get_resource_model())

            # the output resource should be imported
            new_output_process = new_protocol_2.get_process('sink')
            new_output_resource = new_output_process.in_port(Sink.input_name).get_resource_model()
            self.assertIsNotNone(new_output_resource)
