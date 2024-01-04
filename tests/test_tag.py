# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BaseTestCase, Tag, TagHelper
from gws_core.config.config_params import ConfigParams
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.utils.date_helper import DateHelper
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.impl.robot.robot_resource import Robot, RobotFood
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotEat, RobotMove
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.protocol.protocol_interface import IProtocol
from gws_core.report.report_dto import ReportSaveDTO
from gws_core.report.report_service import ReportService
from gws_core.resource.resource_service import ResourceService
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import TagOrigins
from gws_core.tag.tag_dto import EntityTagValueFormat, TagOriginType
from gws_core.tag.tag_key_model import TagKeyModel
from gws_core.tag.tag_service import TagService
from gws_core.tag.tag_value_model import TagValueModel
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService


@task_decorator("TagRobot", human_name="Move robot",
                short_description="This task emulates a short moving step of the robot", hide=True)
class TagRobot(Task):
    input_specs = InputSpecs({'robot': InputSpec(Robot)})
    output_specs = OutputSpecs({'robot': OutputSpec(Robot)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        robot: Robot = inputs['robot']
        robot.tags.add_tag(Tag('robot_tag_propagable', 'robot_value',  is_propagable=True))
        robot.tags.add_tag(Tag('robot_tag_not_propagable', 'robot_value', is_propagable=False))
        return {'robot': robot}


# test_tag
class TestTag(BaseTestCase):

    def test_origin(self):
        tag = Tag('tag', 'value')
        self.assertFalse(tag.origin_is_defined())
        self.assertTrue(tag.origins.add_origin(TagOriginType.USER, 'user_id'))
        self.assertTrue(tag.origin_is_defined())
        self.assertEqual(tag.origins.count_origins(), 1)
        self.assertTrue(tag.origins.has_origin(TagOriginType.USER, 'user_id'))
        self.assertTrue(tag.origins.is_user_origin())

        # add an automatic origin, this should overide the user origin
        self.assertTrue(tag.origins.add_origin(TagOriginType.EXPERIMENT_PROPAGATED, 'exp_id'))
        self.assertEqual(tag.origins.count_origins(), 1)
        self.assertTrue(tag.origins.has_origin(TagOriginType.EXPERIMENT_PROPAGATED, 'exp_id'))

        # add a second origin
        self.assertTrue(tag.origins.add_origin(TagOriginType.TASK_PROPAGATED, 'task_id'))
        self.assertEqual(tag.origins.count_origins(), 2)
        self.assertTrue(tag.origins.has_origin(TagOriginType.EXPERIMENT_PROPAGATED, 'exp_id'))
        self.assertTrue(tag.origins.has_origin(TagOriginType.TASK_PROPAGATED, 'task_id'))

        # add a user origin (should not be added because there is already an automatic origin)
        self.assertFalse(tag.origins.add_origin(TagOriginType.USER, 'user_id'))
        self.assertEqual(tag.origins.count_origins(), 2)
        self.assertTrue(tag.origins.has_origin(TagOriginType.EXPERIMENT_PROPAGATED, 'exp_id'))
        self.assertTrue(tag.origins.has_origin(TagOriginType.TASK_PROPAGATED, 'task_id'))

        # remove an origin
        tag.origins.remove_origin(TagOriginType.EXPERIMENT_PROPAGATED, 'exp_id')
        self.assertEqual(tag.origins.count_origins(), 1)
        self.assertFalse(tag.origins.has_origin(TagOriginType.EXPERIMENT_PROPAGATED, 'exp_id'))

    def test_add_tag(self):
        experiment: Experiment = ExperimentService.create_experiment()

        expected_tag = Tag('test', 'value')

        # Add the tag to the model and check that is was added in DB
        tag = TagService.add_tag_to_entity(EntityType.EXPERIMENT, experiment.id, expected_tag)
        self.assertEqual(tag.entity_type, EntityType.EXPERIMENT)
        self.assertEqual(tag.entity_id, experiment.id)
        self.assertEqual(tag.tag_key, 'test')
        self.assertEqual(tag.tag_value, 'value')

        entity_tags = TagService.find_by_entity_id(EntityType.EXPERIMENT, experiment.id)
        self.assertTrue(len(entity_tags.get_tags()), 0)
        self.assertTrue(entity_tags.has_tag(expected_tag))

        # Check that the tag was added to the tag table
        self.assertTrue(TagValueModel.tag_value_exists('test', 'value'))

        # add int tag
        tag = TagService.add_tag_to_entity(EntityType.EXPERIMENT, experiment.id, Tag('test_int', 1))
        self.assertEqual(tag.get_tag_value(), 1)
        self.assertEqual(TagValueModel.get_tag_value_model('test_int', 1).get_tag_value(), 1)
        self.assertEqual(TagKeyModel.find_by_key('test_int').value_format, EntityTagValueFormat.INTEGER)

        # add float tag
        tag = TagService.add_tag_to_entity(EntityType.EXPERIMENT, experiment.id, Tag('test_float', 1.1))
        self.assertEqual(tag.get_tag_value(), 1.1)
        self.assertEqual(TagValueModel.get_tag_value_model('test_float', 1.1).get_tag_value(), 1.1)
        self.assertEqual(TagKeyModel.find_by_key('test_float').value_format, EntityTagValueFormat.FLOAT)

        # add datetime tag
        now = DateHelper.now_utc()
        tag = TagService.add_tag_to_entity(EntityType.EXPERIMENT, experiment.id, Tag('test_datetime', now))
        self.assertEqual(tag.get_tag_value(), now)
        self.assertEqual(TagValueModel.get_tag_value_model('test_datetime', now).get_tag_value(), now)
        self.assertEqual(TagKeyModel.find_by_key('test_datetime').value_format, EntityTagValueFormat.DATETIME)

    def test_tag_crud(self) -> None:
        """ Test update and delete tag"""

        tag = Tag('newtag', 'value')
        other_tag = Tag('newtag', 'other_value')
        TagService.create_tag(tag.key, tag.value)
        TagService.create_tag(other_tag.key, other_tag.value)

        experiment: Experiment = ExperimentService.create_experiment()
        TagService.add_tag_to_entity(EntityType.EXPERIMENT, experiment.id, tag)

        # test update the tag
        new_tag = Tag('newtag', 'newvalue')
        TagService.update_registered_tag_value(tag.key, tag.value, new_tag.value)

        # Check that the tag model was updated
        self.assertFalse(TagValueModel.tag_value_exists(tag.key, tag.value))
        self.assertTrue(TagValueModel.tag_value_exists(tag.key, new_tag.value))

        experiment_tags = TagService.find_by_entity_id(EntityType.EXPERIMENT, experiment.id)
        self.assertFalse(experiment_tags.has_tag(tag))
        self.assertTrue(experiment_tags.has_tag(new_tag))

        # Test delete tag
        TagService.delete_registered_tag(new_tag.key, new_tag.value)

        # Check that the tag model was delete (because there is no more values)
        self.assertFalse(TagValueModel.tag_value_exists(new_tag.key, new_tag.value))

        experiment_tags = TagService.find_by_entity_id(EntityType.EXPERIMENT, experiment.id)
        self.assertFalse(experiment_tags.has_tag(new_tag))

        # Remove the last value of the TagModel and check that it was deleted (because it is the last value)
        TagService.delete_registered_tag(other_tag.key, other_tag.value)
        tag_model = TagKeyModel.find_by_key(new_tag.key)
        self.assertIsNone(tag_model)

    def test_search(self):
        tag = Tag('first_key', 'first_value')
        other_tag = Tag('second_key', 'second_value')

        # experiment 1 tagged with the 2 tags
        experiment: Experiment = ExperimentService.create_experiment()
        TagService.add_tag_to_entity(EntityType.EXPERIMENT, experiment.id, tag)
        TagService.add_tag_to_entity(EntityType.EXPERIMENT, experiment.id, other_tag)

        # experiment 2 tagged only with the first tag
        experiment_2: Experiment = ExperimentService.create_experiment()
        TagService.add_tag_to_entity(EntityType.EXPERIMENT, experiment_2.id, tag)

        search_dict: SearchParams = SearchParams()

        # search with only second tag
        search_dict.filtersCriteria = [
            {"key": "tags", "operator": "EQ", "value": TagHelper.tags_to_json([other_tag])}]
        paginator = ExperimentService.search(search_dict)
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, experiment.id)

        # search with only second tag value contains
        search_dict.filtersCriteria = [
            {"key": "tags", "operator": "CONTAINS", "value": TagHelper.tags_to_json([Tag('second_key', 'cond_val')])}]
        paginator = ExperimentService.search(search_dict)
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, experiment.id)

        # search with both tags
        search_dict.filtersCriteria = [
            {"key": "tags", "operator": "EQ", "value": TagHelper.tags_to_json([tag, other_tag])}]
        paginator = ExperimentService.search(search_dict)
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, experiment.id)

        # test search with int value
        TagService.add_tag_to_entity(EntityType.EXPERIMENT, experiment.id, Tag('int_tag', 1))
        search_dict.filtersCriteria = [
            {"key": "tags", "operator": "EQ", "value": TagHelper.tags_to_json([Tag('int_tag', 1)])}]
        paginator = ExperimentService.search(search_dict)
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, experiment.id)

        # test search with float value
        # TagService.add_tag_to_entity(EntityType.EXPERIMENT, experiment.id, Tag('float_tag', 1.1))
        # search_dict.filtersCriteria = [
        #     {"key": "tags", "operator": "EQ", "value": TagHelper.tags_to_json([Tag('float_tag', 1.1)])}]
        # paginator = ExperimentService.search(search_dict)
        # self.assertEqual(paginator.page_info.total_number_of_items, 1)
        # self.assertEqual(paginator.results[0].id, experiment.id)

        # test search with datetime value
        now = DateHelper.now_utc()
        TagService.add_tag_to_entity(EntityType.EXPERIMENT, experiment.id, Tag('datetime_tag', now))
        search_dict.filtersCriteria = [{"key": "tags", "operator": "EQ", "value": TagHelper.tags_to_json(
            [Tag('datetime_tag', DateHelper.to_iso_str(now))])}]
        paginator = ExperimentService.search(search_dict)
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, experiment.id)

    def test_tag_propagation_exp(self):

        user_id = CurrentUserService.get_and_check_current_user().id

        # Create all the required tags
        tag_a = Tag('tag_a', 'value_a', is_propagable=True, origins=TagOrigins(TagOriginType.USER, user_id))
        tag_a_1 = Tag('tag_a', 'value_a_1', is_propagable=True, origins=TagOrigins(TagOriginType.USER, user_id))
        tag_b = Tag('tag_b', 'value_b', is_propagable=True, origins=TagOrigins(TagOriginType.USER, user_id))
        tag_exp = Tag('tag_exp', 'value_exp', is_propagable=True, origins=TagOrigins(TagOriginType.USER, user_id))
        tag_r_not_propagable = Tag(
            'tag_r_not', 'value_exp', is_propagable=False, origins=TagOrigins(TagOriginType.USER, user_id))
        tag_exp_not_propagable = Tag(
            'tag_exp_not', 'value_exp', is_propagable=False, origins=TagOrigins(TagOriginType.USER, user_id))

        # Tags created by the TagRobot task
        task_tag_propagable = Tag('robot_tag_propagable', 'robot_value', is_propagable=True)
        task_tag_not_propagable = Tag('robot_tag_not_propagable', 'robot_value', is_propagable=True)

        i_experiment: IExperiment = IExperiment()
        i_experiment.add_tags([tag_exp, tag_exp_not_propagable])
        i_protocol: IProtocol = i_experiment.get_protocol()

        tag_robot = i_protocol.add_process(TagRobot, 'move')
        first_robot = Robot.empty()
        first_robot.tags.add_tags([tag_a, tag_b, tag_r_not_propagable])
        tag_robot.set_input('robot', first_robot)

        eat = i_protocol.add_process(RobotEat, 'eat')
        robot_food = RobotFood.empty()
        robot_food.tags.add_tags([tag_a_1, tag_b])
        eat.set_input('food', robot_food)

        i_protocol.add_connector(tag_robot >> 'robot', eat << 'robot')

        i_experiment.run()

        # Check that the tags are propagated
        tag_robot.refresh()
        eat.refresh()

        # Check that the first output has the tag of first input + exp + 2 tag from task
        first_output = tag_robot.get_output('robot')
        self.assertEqual(len(first_output.tags.get_tags()), 5)

        # Check that the inputs tags were propagated
        self.assertTrue(first_output.tags.has_tag(tag_a))
        self.assertTrue(first_output.tags.has_tag(tag_b))
        self.assertFalse(first_output.tags.has_tag(tag_r_not_propagable))

        # Check detail of propagated tag
        output_tag_a = first_output.tags.get_tag(tag_a.key, tag_a.value)
        self.assertIsNotNone(output_tag_a)
        self.assertTrue(output_tag_a.is_propagable)
        self.assertEqual(output_tag_a.origins.count_origins(), 1)
        self.assertTrue(output_tag_a.origins.has_origin(TagOriginType.TASK_PROPAGATED, tag_robot._process_model.id))

        # Check tag experiment is propagated and values
        output_tag_exp = first_output.tags.get_tag(tag_exp.key, tag_exp.value)
        self.assertIsNotNone(output_tag_exp)
        self.assertTrue(output_tag_exp.is_propagable)
        self.assertEqual(output_tag_exp.origins.count_origins(), 1)
        self.assertTrue(output_tag_exp.origins.has_origin(
            TagOriginType.EXPERIMENT_PROPAGATED, i_experiment.get_experiment_model().id))

        # Check task tags
        ouput_tag_task_propagable = first_output.tags.get_tag(task_tag_propagable.key, task_tag_propagable.value)
        self.assertIsNotNone(ouput_tag_task_propagable)
        self.assertTrue(ouput_tag_task_propagable.is_propagable)
        self.assertEqual(ouput_tag_task_propagable.origins.count_origins(), 1)
        self.assertTrue(ouput_tag_task_propagable.origins.has_origin(TagOriginType.TASK, tag_robot._process_model.id))

        ouput_tag_task_not_propagable = first_output.tags.get_tag(task_tag_not_propagable.key,
                                                                  task_tag_not_propagable.value)
        self.assertIsNotNone(ouput_tag_task_not_propagable)
        self.assertFalse(ouput_tag_task_not_propagable.is_propagable)
        self.assertEqual(ouput_tag_task_not_propagable.origins.count_origins(), 1)
        self.assertTrue(ouput_tag_task_not_propagable.origins.has_origin(
            TagOriginType.TASK, tag_robot._process_model.id))

        # Check that the second output has the tag of all the inputs + exp
        second_output = eat.get_output('robot')
        self.assertEqual(len(second_output.tags.get_tags()), 5)
        self.assertTrue(second_output.tags.has_tag(tag_a))
        self.assertTrue(second_output.tags.has_tag(tag_a_1))
        self.assertTrue(second_output.tags.has_tag(tag_b))
        self.assertTrue(second_output.tags.has_tag(task_tag_propagable))

        # Check tag experiment is propagated
        self.assertTrue(second_output.tags.has_tag(tag_exp))

    def test_tag_propagation_view_report(self):
        propagable_tag = Tag('robot_tag_propagable', 'robot_value', is_propagable=True)

        i_experiment: IExperiment = IExperiment()
        i_experiment.add_tags([propagable_tag])
        i_protocol: IProtocol = i_experiment.get_protocol()

        tag_robot = i_protocol.add_process(RobotEat, 'tag')
        first_robot = Robot.empty()
        tag_robot.set_input('robot', first_robot)

        i_experiment.run()
        tag_robot.refresh()

        experiment_id = i_experiment.get_experiment_model().id

        # Check that the first output has the tag of first input + exp + 2 tag from task
        resource_model = tag_robot.get_output_resource_model('robot')

        # generate a view from this resource
        view_result = ResourceService.get_and_call_view_on_resource_model(resource_model.id, 'view_as_json', {}, True)

        # Check that the tags are propagated
        view_tags = EntityTagList.find_by_entity(EntityType.VIEW, view_result.view_config.id)
        self.assertEqual(len(view_tags.get_tags()), 1)
        self.assertTrue(view_tags.has_tag(propagable_tag))
        tag = view_tags.get_tag(propagable_tag).to_simple_tag()
        self.assertTrue(tag.is_propagable)
        self.assertEqual(tag.origins.count_origins(), 1)
        self.assertTrue(tag.origins.has_origin(TagOriginType.RESOURCE_PROPAGATED, resource_model.id))

        # generate a report and add the view
        report = ReportService.create(ReportSaveDTO(title='test_report'))

        ReportService.add_view_to_content(report.id, view_result.view_config.id)

        # Check that the tags are propagated
        report_tags = EntityTagList.find_by_entity(EntityType.REPORT, report.id)
        self.assertEqual(len(report_tags.get_tags()), 1)
        self.assertTrue(report_tags.has_tag(propagable_tag))
        tag = report_tags.get_tag(propagable_tag).to_simple_tag()
        self.assertTrue(tag.is_propagable)

        # it should have 2 origin, the view and the experiment
        self.assertEqual(tag.origins.count_origins(), 2)
        self.assertTrue(tag.origins.has_origin(TagOriginType.VIEW_PROPAGATED, view_result.view_config.id))
        self.assertTrue(tag.origins.has_origin(TagOriginType.EXPERIMENT_PROPAGATED, experiment_id))

        # if we remove the view from the report, the tag should be kept with 1 origin
        ReportService.update_content(report.id, {"blocks": []})

        report_tags = EntityTagList.find_by_entity(EntityType.REPORT, report.id)
        self.assertEqual(len(report_tags.get_tags()), 1)
        tag = report_tags.get_tag(propagable_tag).to_simple_tag()
        self.assertEqual(tag.origins.count_origins(), 1)
        self.assertTrue(tag.origins.has_origin(TagOriginType.EXPERIMENT_PROPAGATED, experiment_id))

        # Unassociate the experiment from the report, it should delete the tag
        ReportService.remove_experiment(report.id, experiment_id)
        report_tags = EntityTagList.find_by_entity(EntityType.REPORT, report.id)
        self.assertEqual(len(report_tags.get_tags()), 0)

    def test_tag_propagation_after(self):
        i_experiment: IExperiment = IExperiment()
        i_protocol: IProtocol = i_experiment.get_protocol()

        create_robot = i_protocol.add_process(RobotCreate, 'create')
        i_experiment.run()
        exp_1_output = create_robot.refresh().get_output_resource_model('robot')
        exp_1 = i_experiment.get_experiment_model()

        i_experiment_2: IExperiment = IExperiment()
        i_protocol_2: IProtocol = i_experiment_2.get_protocol()
        move_robot = i_protocol_2.add_process(RobotMove, 'move')
        i_protocol_2.add_source('source', exp_1_output.id, move_robot << 'robot')
        i_experiment_2.run()
        exp_2_output = move_robot.refresh().get_output_resource_model('robot')
        exp_2 = i_experiment_2.get_experiment_model()

        # generate a view from this resource
        view_result = ResourceService.get_and_call_view_on_resource_model(exp_2_output.id, 'view_as_json', {}, True)
        exp_2_output_view = view_result.view_config

        # generate a report and add the view
        exp_2_report = ReportService.create(ReportSaveDTO(title='test_report'))
        ReportService.add_view_to_content(exp_2_report.id, exp_2_output_view.id)

        # Now add a tag to the first experiment and check that it is propagated
        new_tag = Tag('manual_tag', 'new_value', is_propagable=True, origins=TagOrigins(TagOriginType.USER, 'user_id'))
        TagService.add_tags_to_entity_and_propagate(EntityType.EXPERIMENT, exp_1.id, [new_tag])

        self._check_propagation_exp_1(exp_1.id, exp_1_output.id, exp_2_output.id, exp_2.id, exp_2_report.id,
                                      exp_2_output_view.id, 1, new_tag, True)

        # add a tag to exp2
        new_tag_2 = Tag('manual_tag_2', 'new_value', is_propagable=True,
                        origins=TagOrigins(TagOriginType.USER, 'user_id'))
        TagService.add_tags_to_entity_and_propagate(EntityType.EXPERIMENT, exp_2.id, [new_tag_2])

        # check that exp1 does not have the tag
        exp_tags = EntityTagList.find_by_entity(EntityType.EXPERIMENT, exp_1)
        self.assertEqual(exp_tags.has_tag(new_tag_2), False)

        # check that the report has the tag with 2 origins (view and exp2)
        report_tags = EntityTagList.find_by_entity(EntityType.REPORT, exp_2_report.id)
        self.assertEqual(report_tags.has_tag(new_tag_2), True)
        tag = report_tags.get_tag(new_tag_2).to_simple_tag()
        self.assertEqual(tag.origins.count_origins(), 2)

        # Delete propagated tag 1
        TagService.delete_tag_from_entity(EntityType.EXPERIMENT, exp_1.id, new_tag.key, new_tag.value)

        self._check_propagation_exp_1(exp_1.id, exp_1_output.id, exp_2_output.id, exp_2.id, exp_2_report.id,
                                      exp_2_output_view.id, 0, new_tag, False)

        # Delete propagated tag 2
        TagService.delete_tag_from_entity(EntityType.EXPERIMENT, exp_2.id, new_tag_2.key, new_tag_2.value)

        # check that the report does not have the tag
        report_tags = EntityTagList.find_by_entity(EntityType.REPORT, exp_2_report.id)
        self.assertEqual(report_tags.has_tag(new_tag_2), False)

    def _check_propagation_exp_1(self, exp_1: str, exp_1_output: str, exp_2_output: str,
                                 exp_2: str, exp_2_report: str, exp_2_output_view: str,
                                 report_origin_count: int,
                                 tag: Tag, should_exist: bool):
        # Check that the tags are propagated
        exp_tags = EntityTagList.find_by_entity(EntityType.EXPERIMENT, exp_1)
        self.assertEqual(exp_tags.has_tag(tag), should_exist)

        # check that resource 1 has the tag
        resource_tags = EntityTagList.find_by_entity(EntityType.RESOURCE, exp_1_output)
        self.assertEqual(resource_tags.has_tag(tag), should_exist)

        # check that resource 2 has the tag
        resource_tags = EntityTagList.find_by_entity(EntityType.RESOURCE, exp_2_output)
        self.assertEqual(resource_tags.has_tag(tag), should_exist)

        # check that exp2 does not have the tag
        exp_tags = EntityTagList.find_by_entity(EntityType.EXPERIMENT, exp_2)
        self.assertEqual(exp_tags.has_tag(tag), False)

        # check that view has the tag
        view_tags = EntityTagList.find_by_entity(EntityType.VIEW, exp_2_output_view)
        self.assertEqual(view_tags.has_tag(tag), should_exist)

        # check that report has the tag with 1 origins (view)
        report_tags = EntityTagList.find_by_entity(EntityType.REPORT, exp_2_report)
        self.assertEqual(report_tags.has_tag(tag), should_exist)

        if should_exist:
            tag = report_tags.get_tag(tag).to_simple_tag()
            self.assertEqual(tag.origins.count_origins(), report_origin_count)
