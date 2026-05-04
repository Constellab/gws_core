from gws_core import BaseTestCase, Tag
from gws_core.core.classes.search_builder import SearchOperator
from gws_core.core.utils.date_helper import DateHelper
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.tag.entity_with_tag_search_builder import EntityWithTagSearchBuilder
from gws_core.tag.tag import TagOrigin, TagOrigins
from gws_core.tag.tag_dto import TagOriginType, TagValueEditDTO, TagValueFormat
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.tag_key_model import TagKeyModel
from gws_core.tag.tag_service import TagService
from gws_core.tag.tag_value_model import TagValueModel


# test_tag
class TestTag(BaseTestCase):
    def test_tag(self):
        # test string tag
        tag = Tag("tag", "value")
        self.assertEqual(tag.key, "tag")
        self.assertEqual(tag.value, "value")
        self.assertEqual(tag.get_value_format(), TagValueFormat.STRING)
        new_tag = Tag.from_dto(tag.to_dto())
        self.assertEqual(new_tag.key, tag.key)
        self.assertEqual(new_tag.value, tag.value)
        self.assertEqual(new_tag.get_value_format(), TagValueFormat.STRING)

        # create a tag with a invalid string
        with self.assertRaises(ValueError):
            Tag("tag#", "value")
        tag = Tag("tag#é", "value#é", auto_parse=True)
        self.assertEqual(tag.key, "tag_e")

        # test int tag
        tag = Tag("tag", 1)
        self.assertEqual(tag.get_value_format(), TagValueFormat.INTEGER)
        new_tag = Tag.from_dto(tag.to_dto())
        self.assertEqual(new_tag.value, tag.value)
        self.assertEqual(new_tag.get_value_format(), TagValueFormat.INTEGER)

        # test float tag
        tag = Tag("tag", 1.1)
        self.assertEqual(tag.get_value_format(), TagValueFormat.FLOAT)
        new_tag = Tag.from_dto(tag.to_dto())
        self.assertEqual(new_tag.value, tag.value)
        self.assertEqual(new_tag.get_value_format(), TagValueFormat.FLOAT)

        # test datetime tag
        now = DateHelper.now_utc()
        tag = Tag("tag", now)
        self.assertEqual(tag.get_value_format(), TagValueFormat.DATETIME)
        new_tag = Tag.from_dto(tag.to_dto())
        self.assertEqual(new_tag.value, tag.value)
        self.assertEqual(new_tag.get_value_format(), TagValueFormat.DATETIME)

    def test_origin(self):
        tag = Tag("tag", "value")
        self.assertFalse(tag.origin_is_defined())
        self.assertTrue(tag.origins.add_origin(TagOrigin(TagOriginType.USER, "user_id")))
        self.assertTrue(tag.origin_is_defined())
        self.assertEqual(tag.origins.count_origins(), 1)
        self.assertTrue(tag.origins.has_origin(TagOriginType.USER, "user_id"))
        self.assertTrue(tag.origins.is_user_origin())

        # add an automatic origin, this should overide the user origin
        self.assertTrue(
            tag.origins.add_origin(TagOrigin(TagOriginType.SCENARIO_PROPAGATED, "exp_id"))
        )
        self.assertEqual(tag.origins.count_origins(), 1)
        self.assertTrue(tag.origins.has_origin(TagOriginType.SCENARIO_PROPAGATED, "exp_id"))

        # add a second origin
        self.assertTrue(tag.origins.add_origin(TagOrigin(TagOriginType.TASK_PROPAGATED, "task_id")))
        self.assertEqual(tag.origins.count_origins(), 2)
        self.assertTrue(tag.origins.has_origin(TagOriginType.SCENARIO_PROPAGATED, "exp_id"))
        self.assertTrue(tag.origins.has_origin(TagOriginType.TASK_PROPAGATED, "task_id"))

        # add a user origin (should not be added because there is already an automatic origin)
        self.assertFalse(tag.origins.add_origin(TagOrigin(TagOriginType.USER, "user_id")))
        self.assertEqual(tag.origins.count_origins(), 2)
        self.assertTrue(tag.origins.has_origin(TagOriginType.SCENARIO_PROPAGATED, "exp_id"))
        self.assertTrue(tag.origins.has_origin(TagOriginType.TASK_PROPAGATED, "task_id"))

        # remove an origin
        tag.origins.remove_origin(TagOriginType.SCENARIO_PROPAGATED, "exp_id")
        self.assertEqual(tag.origins.count_origins(), 1)
        self.assertFalse(tag.origins.has_origin(TagOriginType.SCENARIO_PROPAGATED, "exp_id"))

    def test_add_tag(self):
        scenario: Scenario = ScenarioService.create_scenario()

        expected_tag = Tag("test", "value")

        # Add the tag to the model and check that is was added in DB
        tag = TagService.add_tag_to_entity(TagEntityType.SCENARIO, scenario.id, expected_tag)
        self.assertEqual(tag.entity_type, TagEntityType.SCENARIO)
        self.assertEqual(tag.entity_id, scenario.id)
        self.assertEqual(tag.tag_key, "test")
        self.assertEqual(tag.tag_value, "value")

        entity_tags = TagService.find_by_entity_id(TagEntityType.SCENARIO, scenario.id)
        self.assertTrue(len(entity_tags.get_tags()), 0)
        self.assertTrue(entity_tags.has_tag(expected_tag))

        # Check that the tag was added to the tag table
        self.assertTrue(TagValueModel.tag_value_exists("test", "value"))

        # add int tag
        tag = TagService.add_tag_to_entity(TagEntityType.SCENARIO, scenario.id, Tag("test_int", 1))
        self.assertEqual(tag.get_tag_value(), 1)
        self.assertEqual(TagValueModel.get_tag_value_model("test_int", 1).get_tag_value(), 1)
        self.assertEqual(TagKeyModel.find_by_key("test_int").value_format, TagValueFormat.INTEGER)

        # add float tag
        tag = TagService.add_tag_to_entity(
            TagEntityType.SCENARIO, scenario.id, Tag("test_float", 1.1)
        )
        self.assertEqual(tag.get_tag_value(), 1.1)
        self.assertEqual(TagValueModel.get_tag_value_model("test_float", 1.1).get_tag_value(), 1.1)
        self.assertEqual(TagKeyModel.find_by_key("test_float").value_format, TagValueFormat.FLOAT)

        # add datetime tag
        now = DateHelper.now_utc()
        tag = TagService.add_tag_to_entity(
            TagEntityType.SCENARIO, scenario.id, Tag("test_datetime", now)
        )
        self.assertEqual(tag.get_tag_value(), now)
        self.assertEqual(
            TagValueModel.get_tag_value_model("test_datetime", now).get_tag_value(), now
        )
        self.assertEqual(
            TagKeyModel.find_by_key("test_datetime").value_format, TagValueFormat.DATETIME
        )

    def test_tag_crud(self) -> None:
        """Test update and delete tag"""

        tag = Tag("newtag", "value")
        other_tag = Tag("newtag", "other_value")

        TagService.create_tag(tag.key, tag.value)
        TagService.create_tag(other_tag.key, other_tag.value)

        scenario: Scenario = ScenarioService.create_scenario()
        TagService.add_tag_to_entity(TagEntityType.SCENARIO, scenario.id, tag)

        # test update the tag
        new_tag = Tag("newtag", "newvalue")
        TagService.update_registered_tag_value(tag.key, tag.value, new_tag.value)

        # Check that the tag model was updated
        self.assertFalse(TagValueModel.tag_value_exists(tag.key, tag.value))
        self.assertTrue(TagValueModel.tag_value_exists(tag.key, new_tag.value))

        scenario_tags = TagService.find_by_entity_id(TagEntityType.SCENARIO, scenario.id)
        self.assertFalse(scenario_tags.has_tag(tag))
        self.assertTrue(scenario_tags.has_tag(new_tag))

        # Test delete tag
        TagService.delete_registered_tag(new_tag.key, new_tag.value)

        # Check that the tag model was delete (because there is no more values)
        self.assertFalse(TagValueModel.tag_value_exists(new_tag.key, new_tag.value))

        scenario_tags = TagService.find_by_entity_id(TagEntityType.SCENARIO, scenario.id)
        self.assertFalse(scenario_tags.has_tag(new_tag))

        # Remove the last value of the TagModel and check that it was deleted (because it is the last value)
        TagService.delete_registered_tag(other_tag.key, other_tag.value)
        tag_model = TagKeyModel.find_by_key(new_tag.key)
        self.assertIsNone(tag_model)

    def test_search(self):
        tag = Tag("first_key", "first_value")
        other_tag = Tag("second_key", "second_value")

        # scenario 1 tagged with the 2 tags
        scenario: Scenario = ScenarioService.create_scenario()
        TagService.add_tag_to_entity(TagEntityType.SCENARIO, scenario.id, tag)
        TagService.add_tag_to_entity(TagEntityType.SCENARIO, scenario.id, other_tag)

        # scenario 2 tagged only with the first tag
        scenario_2: Scenario = ScenarioService.create_scenario()
        TagService.add_tag_to_entity(TagEntityType.SCENARIO, scenario_2.id, tag)

        result = TagService.get_entities_by_tag(TagEntityType.SCENARIO, tag)
        self.assertEqual(len(result), 2)

        search_builder = EntityWithTagSearchBuilder(Scenario, TagEntityType.SCENARIO)
        search_builder.add_tag_filter(other_tag)
        scenarios = search_builder.search_all()
        self.assertEqual(len(scenarios), 1)
        self.assertEqual(scenarios[0].id, scenario.id)

        # search with only second tag value contains
        search_builder = EntityWithTagSearchBuilder(Scenario, TagEntityType.SCENARIO)
        search_builder.add_tag_filter(Tag("second_key", "cond_val"), SearchOperator.CONTAINS)
        scenarios = search_builder.search_all()
        self.assertEqual(len(scenarios), 1)
        self.assertEqual(scenarios[0].id, scenario.id)

        # search with both tags
        search_builder = EntityWithTagSearchBuilder(Scenario, TagEntityType.SCENARIO)
        search_builder.add_tag_filter(tag)
        search_builder.add_tag_filter(other_tag)
        scenarios = search_builder.search_all()
        self.assertEqual(len(scenarios), 1)
        self.assertEqual(scenarios[0].id, scenario.id)

        # search with tag key only
        search_builder = EntityWithTagSearchBuilder(Scenario, TagEntityType.SCENARIO)
        search_builder.add_tag_key_filter("first_key")
        scenarios = search_builder.search_all()
        self.assertEqual(len(scenarios), 2)

        # test search with int value
        # TagService.add_tag_to_entity(EntityType.SCENARIO, scenario.id, Tag('int_tag', 1))
        # search_dict.set_filters_criteria([
        #     SearchFilterCriteria(
        #         key="tags", operator=SearchOperator.EQ, value=TagHelper.tags_to_json(
        #             [Tag('int_tag', 1)]))])
        # paginator = ScenarioService.search(search_dict)
        # self.assertEqual(paginator.page_info.total_number_of_items, 1)
        # self.assertEqual(paginator.results[0].id, scenario.id)

        # # test search with datetime value
        # now = DateHelper.now_utc()
        # TagService.add_tag_to_entity(EntityType.SCENARIO, scenario.id, Tag('datetime_tag', now))
        # search_dict.set_filters_criteria([
        #     SearchFilterCriteria(
        #         key="tags", operator=SearchOperator.EQ, value=TagHelper.tags_to_json(
        #             [Tag('datetime_tag', now)]))])
        # paginator = ScenarioService.search(search_dict)
        # self.assertEqual(paginator.page_info.total_number_of_items, 1)
        # self.assertEqual(paginator.results[0].id, scenario.id)

    def test_tag_key(self):
        # Create a tag key with a valid key
        tag_key = TagService.create_tag_key("test_key", "Test key")
        self.assertIsNotNone(tag_key)
        self.assertEqual(tag_key.key, "test_key")
        self.assertEqual(tag_key.value_format, TagValueFormat.STRING)
        self.assertEqual(tag_key.label, "Test key")

        # Try to create a tag key with an invalid key
        with self.assertRaises(ValueError):
            TagService.create_tag_key("invalid#key", "Label")

        # Try to create a tag key with an existing key
        with self.assertRaises(ValueError):
            TagService.create_tag_key("test_key", "Label")

    def test_tag_value(self):
        tag_key = TagService.create_tag_key("test_key_for_value", "Test key")

        # Create a tag value with a valid key and value
        tag_value = TagService.create_tag_value(
            TagValueEditDTO(value="test_value", tag_key=tag_key.key)
        )
        self.assertIsNotNone(tag_value)
        self.assertEqual(tag_value.tag_key.key, "test_key_for_value")
        self.assertEqual(tag_value.tag_value, "test_value")

        # Try to create a tag value with an invalid key
        with self.assertRaises(ValueError):
            TagService.create_tag_value(TagValueEditDTO(value="value", tag_key="invalid_key"))

        # Try to create a tag value with an existing key and value
        with self.assertRaises(ValueError):
            TagService.create_tag_value(TagValueEditDTO(value="test_value", tag_key=tag_key.key))
