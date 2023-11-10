# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BaseTestCase, Tag, TagHelper
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.utils.date_helper import DateHelper
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.impl.robot.robot_resource import Robot, RobotFood
from gws_core.impl.robot.robot_tasks import RobotEat, RobotMove
from gws_core.protocol.protocol_interface import IProtocol
from gws_core.tag.entity_tag import EntityTagType
from gws_core.tag.tag import KEY_VALUE_SEPARATOR, TAGS_SEPARATOR
from gws_core.tag.tag_model import EntityTagValueFormat, TagModel
from gws_core.tag.tag_service import TagService


# test_tag
class TestTag(BaseTestCase):

    def test_tag(self):
        tag = Tag('test', 'value')

        tag_str = 'test' + KEY_VALUE_SEPARATOR + 'value'
        self.assertEqual(str(tag), tag_str)

        tag2 = Tag.from_string(tag_str)
        self.assertEqual(tag, tag2)

    def test_tag_helper(self):
        tag = Tag('test', 'value')
        tag2 = Tag('test2', 'value2')
        tag_list = [tag, tag2]

        # Check the tag list to string and from string
        tag_list_str = TAGS_SEPARATOR + str(tag) + TAGS_SEPARATOR + str(tag2) + TAGS_SEPARATOR
        self.assertEqual(TagHelper.tags_to_str(tag_list), tag_list_str)
        self.assertEqual(tag_list, TagHelper.tags_to_list(tag_list_str))

        # Test add tag to list
        new_list = TagHelper.add_or_replace_tag(tag_list_str, 'new_tag', 'new_value')
        new_list_expected = tag_list_str + str(Tag('new_tag', 'new_value')) + TAGS_SEPARATOR
        self.assertEqual(new_list, new_list_expected)

        # Test modify a tag in list
        new_list_2 = TagHelper.add_or_replace_tag(tag_list_str, 'test2', 'OK')
        new_list_expected_2 = TAGS_SEPARATOR + str(tag) + TAGS_SEPARATOR + str(Tag('test2', 'OK')) + TAGS_SEPARATOR
        self.assertEqual(new_list_2, new_list_expected_2)

    def test_add_tag(self):
        experiment: Experiment = ExperimentService.create_experiment()

        expected_tag = Tag('test', 'value')

        # Add the tag to the model and check that is was added in DB
        tag = TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, 'test', 'value')
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
        tag = TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, 'test_int', 1)
        self.assertEqual(tag.get_tag_value(), 1)
        tag_model = TagModel.find_by_key('test_int')
        self.assertEqual(tag_model.values, [1])
        self.assertEqual(tag_model.value_format, EntityTagValueFormat.INTEGER)

        # add float tag
        tag = TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, 'test_float', 1.1)
        self.assertEqual(tag.get_tag_value(), 1.1)
        tag_model = TagModel.find_by_key('test_float')
        self.assertEqual(tag_model.values, [1.1])
        self.assertEqual(tag_model.value_format, EntityTagValueFormat.FLOAT)

        # add datetime tag
        now = DateHelper.now_utc()
        tag = TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, 'test_datetime', now)
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
        TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, tag.key, tag.value)

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
        TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, tag.key, tag.value)
        TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, other_tag.key, other_tag.value)

        # experiment 2 tagged only with the first tag
        experiment_2: Experiment = ExperimentService.create_experiment()
        TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment_2.id, tag.key, tag.value)

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
        TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, 'int_tag', 1)
        search_dict.filtersCriteria = [
            {"key": "tags", "operator": "EQ", "value": TagHelper.tags_to_json([Tag('int_tag', 1)])}]
        paginator = ExperimentService.search(search_dict)
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, experiment.id)

        # test search with float value
        # TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, 'float_tag', 1.1)
        # search_dict.filtersCriteria = [
        #     {"key": "tags", "operator": "EQ", "value": TagHelper.tags_to_json([Tag('float_tag', 1.1)])}]
        # paginator = ExperimentService.search(search_dict)
        # self.assertEqual(paginator.page_info.total_number_of_items, 1)
        # self.assertEqual(paginator.results[0].id, experiment.id)

        # test search with datetime value
        now = DateHelper.now_utc()
        TagService.add_tag_to_entity(EntityTagType.EXPERIMENT, experiment.id, 'datetime_tag', now)
        search_dict.filtersCriteria = [{"key": "tags", "operator": "EQ", "value": TagHelper.tags_to_json(
            [Tag('datetime_tag', DateHelper.to_iso_str(now))])}]
        paginator = ExperimentService.search(search_dict)
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, experiment.id)

    def test_tag_propagation(self):

        tag_a = Tag('tag_a', 'value_a')
        tag_a_1 = Tag('tag_a', 'value_a_1')
        tag_b = Tag('tag_b', 'value_b')

        i_experiment: IExperiment = IExperiment()
        i_protocol: IProtocol = i_experiment.get_protocol()

        move = i_protocol.add_process(RobotMove, 'move')
        first_robot = Robot.empty()
        first_robot.tags.add_tags([tag_a, tag_b])
        move.set_input('robot', first_robot)

        eat = i_protocol.add_process(RobotEat, 'eat')
        robot_food = RobotFood.empty()
        robot_food.tags.add_tags([tag_a_1, tag_b])
        eat.set_input('food', robot_food)

        i_protocol.add_connector(move >> 'robot', eat << 'robot')

        i_experiment.run()

        # Check that the tags are propagated
        move.refresh()
        eat.refresh()

        first_output = move.get_output('robot')
        self.assertTrue(first_output.tags.has_tag(tag_a))
        self.assertTrue(first_output.tags.has_tag(tag_b))

        second_output = eat.get_output('robot')
        self.assertEqual(len(second_output.tags.get_tags()), 3)
        self.assertTrue(second_output.tags.has_tag(tag_a))
        self.assertTrue(second_output.tags.has_tag(tag_a_1))
        self.assertTrue(second_output.tags.has_tag(tag_b))
