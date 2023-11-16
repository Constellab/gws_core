# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BaseTestCase, Tag, TagHelper
from gws_core.config.config_params import ConfigParams
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.utils.date_helper import DateHelper
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.impl.robot.robot_resource import Robot, RobotFood
from gws_core.impl.robot.robot_tasks import RobotEat
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.protocol.protocol_interface import IProtocol
from gws_core.tag.entity_tag import EntityTagType
from gws_core.tag.tag import TagOriginType
from gws_core.tag.tag_model import EntityTagValueFormat, TagModel
from gws_core.tag.tag_service import TagService
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

    def test_add_tag(self):
        experiment: Experiment = ExperimentService.create_experiment()

        expected_tag = Tag('test', 'value')

        # Add the tag to the model and check that is was added in DB
        tag = TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, expected_tag)
        self.assertEqual(tag.entity_type, EntityTagType.EXPERIMENT.value)
        self.assertEqual(tag.entity_id, experiment.id)
        self.assertEqual(tag.tag_key_id, 'test')
        self.assertEqual(tag.tag_value, 'value')

        entity_tags = TagService.find_by_entity_id(EntityTagType.EXPERIMENT, experiment.id)
        self.assertTrue(len(entity_tags.get_tags()), 0)
        self.assertTrue(entity_tags.has_tag(expected_tag))

        # Check that the tag was added to the tag table
        tag_model = TagModel.find_by_key('test')
        self.assertEqual(tag_model.values, ['value'])

        # add value to tag model
        tag_model.add_value('value2')
        self.assertEqual(tag_model.values, ['value', 'value2'])

        # add an existing value
        tag_model.add_value('value')
        self.assertEqual(tag_model.values, ['value', 'value2'])

        # add int tag
        tag = TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, Tag('test_int', 1))
        self.assertEqual(tag.get_tag_value(), 1)
        tag_model = TagModel.find_by_key('test_int')
        self.assertEqual(tag_model.values, [1])
        self.assertEqual(tag_model.value_format, EntityTagValueFormat.INTEGER)

        # add float tag
        tag = TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, Tag('test_float', 1.1))
        self.assertEqual(tag.get_tag_value(), 1.1)
        tag_model = TagModel.find_by_key('test_float')
        self.assertEqual(tag_model.values, [1.1])
        self.assertEqual(tag_model.value_format, EntityTagValueFormat.FLOAT)

        # add datetime tag
        now = DateHelper.now_utc()
        tag = TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, Tag('test_datetime', now))
        self.assertEqual(tag.get_tag_value(), now)
        tag_model = TagModel.find_by_key('test_datetime')
        self.assertEqual(tag_model.values, [now])
        self.assertEqual(tag_model.value_format, EntityTagValueFormat.DATETIME)

        # test to json TODO
        # self.assertIsNotNone(resource_model_db.to_json()['tags'])

    def test_tag_crud(self) -> None:
        """ Test update and delete tag"""

        tag = Tag('newtag', 'value')
        other_tag = Tag('newtag', 'other_value')
        TagService.register_tag(tag.key, tag.value)
        TagService.register_tag(other_tag.key, other_tag.value)

        experiment: Experiment = ExperimentService.create_experiment()
        TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, tag)

        # test update the tag
        new_tag = Tag('newtag', 'newvalue')
        TagService.update_registered_tag_value(tag.key, tag.value, new_tag.value)

        # Check that the tag model was updated
        tag_model: TagModel = TagModel.find_by_key(tag.key)
        self.assertFalse(tag_model.has_value(tag.value))
        self.assertTrue(tag_model.has_value(new_tag.value))

        experiment_tags = TagService.find_by_entity_id(EntityTagType.EXPERIMENT, experiment.id)
        self.assertFalse(experiment_tags.has_tag(tag))
        self.assertTrue(experiment_tags.has_tag(new_tag))

        # Test delete tag
        TagService.delete_registered_tag(new_tag.key, new_tag.value)

        # Check that the tag model was delete (because there is no more values)
        tag_model = TagModel.find_by_key(new_tag.key)
        self.assertFalse(tag_model.has_value(new_tag.value))

        experiment_tags = TagService.find_by_entity_id(EntityTagType.EXPERIMENT, experiment.id)
        self.assertFalse(experiment_tags.has_tag(new_tag))

        # Remove the last value of the TagModel and check that it was deleted (because it is the last value)
        TagService.delete_registered_tag(other_tag.key, other_tag.value)
        tag_model = TagModel.find_by_key(new_tag.key)
        self.assertIsNone(tag_model)

    def test_search(self):
        tag = Tag('first_key', 'first_value')
        other_tag = Tag('second_key', 'second_value')

        # experiment 1 tagged with the 2 tags
        experiment: Experiment = ExperimentService.create_experiment()
        TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, tag)
        TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, other_tag)

        # experiment 2 tagged only with the first tag
        experiment_2: Experiment = ExperimentService.create_experiment()
        TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment_2.id, tag)

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
        TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, Tag('int_tag', 1))
        search_dict.filtersCriteria = [
            {"key": "tags", "operator": "EQ", "value": TagHelper.tags_to_json([Tag('int_tag', 1)])}]
        paginator = ExperimentService.search(search_dict)
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, experiment.id)

        # test search with float value
        # TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, Tag('float_tag', 1.1))
        # search_dict.filtersCriteria = [
        #     {"key": "tags", "operator": "EQ", "value": TagHelper.tags_to_json([Tag('float_tag', 1.1)])}]
        # paginator = ExperimentService.search(search_dict)
        # self.assertEqual(paginator.page_info.total_number_of_items, 1)
        # self.assertEqual(paginator.results[0].id, experiment.id)

        # test search with datetime value
        now = DateHelper.now_utc()
        TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, Tag('datetime_tag', now))
        search_dict.filtersCriteria = [{"key": "tags", "operator": "EQ", "value": TagHelper.tags_to_json(
            [Tag('datetime_tag', DateHelper.to_iso_str(now))])}]
        paginator = ExperimentService.search(search_dict)
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, experiment.id)

    def test_tag_propagation(self):

        # Create all the required tags
        tag_a = Tag('tag_a', 'value_a', is_propagable=True, origin_type=TagOriginType.USER,
                    origin_id=CurrentUserService.get_and_check_current_user().id)
        tag_a_1 = Tag('tag_a', 'value_a_1', is_propagable=True, origin_type=TagOriginType.USER,
                      origin_id=CurrentUserService.get_and_check_current_user().id)
        tag_b = Tag('tag_b', 'value_b', is_propagable=True, origin_type=TagOriginType.USER,
                    origin_id=CurrentUserService.get_and_check_current_user().id)
        tag_exp = Tag('tag_exp', 'value_exp', is_propagable=True, origin_type=TagOriginType.USER,
                      origin_id=CurrentUserService.get_and_check_current_user().id)
        tag_r_not_propagable = Tag(
            'tag_r_not', 'value_exp', is_propagable=False, origin_type=TagOriginType.USER,
            origin_id=CurrentUserService.get_and_check_current_user().id)
        tag_exp_not_propagable = Tag(
            'tag_exp_not', 'value_exp', is_propagable=False, origin_type=TagOriginType.USER,
            origin_id=CurrentUserService.get_and_check_current_user().id)

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
        self.assertEqual(output_tag_a.origin_type, TagOriginType.TASK_PROPAGATED)
        self.assertEqual(output_tag_a.origin_id, tag_robot._process_model.id)

        # Check tag experiment is propagated and values
        output_tag_exp = first_output.tags.get_tag(tag_exp.key, tag_exp.value)
        self.assertIsNotNone(output_tag_exp)
        self.assertTrue(output_tag_exp.is_propagable)
        self.assertEqual(output_tag_exp.origin_type, TagOriginType.EXPERIMENT_PROPAGATED)
        self.assertEqual(output_tag_exp.origin_id, i_experiment.get_experiment_model().id)

        # Check task tags
        ouput_tag_task_propagable = first_output.tags.get_tag(task_tag_propagable.key, task_tag_propagable.value)
        self.assertIsNotNone(ouput_tag_task_propagable)
        self.assertTrue(ouput_tag_task_propagable.is_propagable)
        self.assertEqual(ouput_tag_task_propagable.origin_type, TagOriginType.TASK)
        self.assertEqual(ouput_tag_task_propagable.origin_id, tag_robot._process_model.id)

        ouput_tag_task_not_propagable = first_output.tags.get_tag(task_tag_not_propagable.key,
                                                                  task_tag_not_propagable.value)
        self.assertIsNotNone(ouput_tag_task_not_propagable)
        self.assertFalse(ouput_tag_task_not_propagable.is_propagable)
        self.assertEqual(ouput_tag_task_not_propagable.origin_type, TagOriginType.TASK)
        self.assertEqual(ouput_tag_task_not_propagable.origin_id, tag_robot._process_model.id)

        # Check that the second output has the tag of all the inputs + exp
        second_output = eat.get_output('robot')
        self.assertEqual(len(second_output.tags.get_tags()), 5)
        self.assertTrue(second_output.tags.has_tag(tag_a))
        self.assertTrue(second_output.tags.has_tag(tag_a_1))
        self.assertTrue(second_output.tags.has_tag(tag_b))
        self.assertTrue(second_output.tags.has_tag(task_tag_propagable))

        # Check tag experiment is propagated
        self.assertTrue(second_output.tags.has_tag(tag_exp))
