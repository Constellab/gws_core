from peewee import Expression

from gws_core.core.classes.search_builder import SearchFilterCriteria
from gws_core.form.form import Form
from gws_core.form.form_dto import FormStatus
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.tag.entity_with_tag_search_builder import EntityWithTagSearchBuilder
from gws_core.tag.tag_entity_type import TagEntityType


class FormSearchBuilder(EntityWithTagSearchBuilder[Form]):
    def __init__(self) -> None:
        super().__init__(
            Form,
            TagEntityType.FORM,
            default_orders=[Form.last_modified_at.desc()],
        )

    def convert_filter_to_expression(
        self, filter_: SearchFilterCriteria
    ) -> Expression | None:
        # template_id isn't a column on Form (Form points at template_version);
        # resolve it through the join to FormTemplateVersion.
        if filter_.key == "template_id":
            return self._handle_template_id_filter(filter_)
        return super().convert_filter_to_expression(filter_)

    def add_status_filter(self, status: FormStatus) -> "FormSearchBuilder":
        self.add_expression(Form.status == status)
        return self

    def add_template_id_filter(self, template_id: str) -> "FormSearchBuilder":
        """Filter forms whose underlying FormTemplateVersion belongs to the
        given template (across all versions of that template)."""
        self.add_expression(
            Form.template_version.in_(
                FormTemplateVersion.select(FormTemplateVersion.id).where(
                    FormTemplateVersion.template == template_id
                )
            )
        )
        return self

    def _handle_template_id_filter(
        self, filter_: SearchFilterCriteria
    ) -> Expression | None:
        self.add_template_id_filter(filter_.value)
        return None
