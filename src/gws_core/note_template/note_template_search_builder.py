from peewee import Expression

from gws_core.core.classes.search_builder import SearchFilterCriteria
from gws_core.note_template.note_template import NoteTemplate
from gws_core.note_template.note_template_form_template_model import (
    NoteTemplateFormTemplateModel,
)
from gws_core.tag.entity_with_tag_search_builder import EntityWithTagSearchBuilder
from gws_core.tag.tag_entity_type import TagEntityType


class NoteTemplateSearchBuilder(EntityWithTagSearchBuilder[NoteTemplate]):
    def __init__(self) -> None:
        super().__init__(NoteTemplate, TagEntityType.NOTE_TEMPLATE, default_orders=[NoteTemplate.last_modified_at.desc()])

    def convert_filter_to_expression(
        self, filter_: SearchFilterCriteria
    ) -> Expression | None:
        # form_template_id isn't a column on NoteTemplate; resolve it through
        # the NoteTemplateFormTemplateModel join table.
        if filter_.key == "form_template_id":
            self.add_form_template_filter(filter_.value)
            return None
        return super().convert_filter_to_expression(filter_)

    def add_form_template_filter(self, form_template_id: str) -> None:
        """Filter note templates that embed any version of the given form
        template via the NoteTemplateFormTemplateModel join table.

        Uses an uncorrelated IN subquery so a note template matches at most
        once even when it embeds multiple versions of the same template.

        :param form_template_id: Id of the FormTemplate to filter by.
        :type form_template_id: str
        """
        self.add_expression(
            NoteTemplate.id.in_(
                NoteTemplateFormTemplateModel.select(
                    NoteTemplateFormTemplateModel.note_template
                ).where(
                    NoteTemplateFormTemplateModel.form_template == form_template_id
                )
            )
        )
