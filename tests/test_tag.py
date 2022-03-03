
from gws_core import BaseTestCase, Tag, TagHelper
from gws_core.impl.robot.robot_resource import Robot
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.tag.tag import KEY_VALUE_SEPARATOR, TAGS_SEPARATOR
from gws_core.tag.tag_model import TagModel
from gws_core.tag.tag_service import TagService


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
        tag_list_str = str(tag) + TAGS_SEPARATOR + str(tag2)
        self.assertEqual(TagHelper.tags_to_str(tag_list), tag_list_str)
        self.assertEqual(tag_list, TagHelper.tags_to_list(tag_list_str))

        # Test add tag to list
        new_list = TagHelper.add_or_replace_tag(tag_list_str, 'new_tag', 'new_value')
        new_list_expected = tag_list_str + TAGS_SEPARATOR + str(Tag('new_tag', 'new_value'))
        self.assertEqual(new_list, new_list_expected)

        # Test modify a tag in list
        new_list_2 = TagHelper.add_or_replace_tag(tag_list_str, 'test2', 'OK')
        new_list_expected_2 = str(tag) + TAGS_SEPARATOR + str(Tag('test2', 'ok'))
        self.assertEqual(new_list_2, new_list_expected_2)

    def test_add_tag(self):
        robot: Robot = Robot.empty()
        resource_model = ResourceModel.save_from_resource(robot, origin=ResourceOrigin.UPLOADED)

        expected_tags = [Tag('Test', 'value')]

        # Add the tag to the model and check that is was added in DB
        tags = TagService.add_tag_to_model(resource_model.typing_name, resource_model.id, 'Test', 'value')
        self.assertEqual(tags, expected_tags)
        resource_model_db: ResourceModel = ResourceModel.get_by_id_and_check(resource_model.id)
        self.assertEqual(resource_model_db.get_tags(), expected_tags)

        # Check that the tag was added to the tag table
        tag_model = TagModel.find_by_key('Test')
        self.assertEqual(tag_model.values, ['value'])

        # add value to tag model
        tag_model.add_value('value2')
        self.assertEqual(tag_model.values, ['value', 'value2'])

        # add an existing value
        tag_model.add_value('value')
        self.assertEqual(tag_model.values, ['value', 'value2'])

        # test to json
        self.assertIsNotNone(resource_model_db.to_json()['tags'])
