from gws_core.tag.tag_list import TagList


class TagListField:
    """Class similare to a RField to lazy load the tags of a resource"""

    def load_tags(self, resource_model_id: str | None = None) -> TagList:
        from gws_core.tag.entity_tag_list import EntityTagList
        from gws_core.tag.tag_entity_type import TagEntityType

        if resource_model_id is None:
            return TagList()
        entity_tag_list = EntityTagList.find_by_entity(TagEntityType.RESOURCE, resource_model_id)
        tag_list = [entity_tag.to_simple_tag() for entity_tag in entity_tag_list.get_tags()]

        # set the flag to know if the tag is loaded from the database
        for tag in tag_list:
            tag.__is_field_loaded__ = True
        return TagList(tag_list)
