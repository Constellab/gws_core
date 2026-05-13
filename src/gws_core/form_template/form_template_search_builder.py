from gws_core.form_template.form_template import FormTemplate
from gws_core.tag.entity_with_tag_search_builder import EntityWithTagSearchBuilder
from gws_core.tag.tag_entity_type import TagEntityType


class FormTemplateSearchBuilder(EntityWithTagSearchBuilder[FormTemplate]):
    def __init__(self) -> None:
        super().__init__(
            FormTemplate,
            TagEntityType.FORM_TEMPLATE,
            default_orders=[FormTemplate.last_modified_at.desc()],
        )
