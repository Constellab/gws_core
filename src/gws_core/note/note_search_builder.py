from peewee import Expression

from gws_core.core.classes.search_builder import SearchFilterCriteria
from gws_core.form.form import Form
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.note.note import Note
from gws_core.note.note_form_model import NoteFormModel
from gws_core.tag.entity_with_tag_search_builder import EntityWithTagSearchBuilder
from gws_core.tag.tag_entity_type import TagEntityType


class NoteSearchBuilder(EntityWithTagSearchBuilder[Note]):
    def __init__(self) -> None:
        super().__init__(Note, TagEntityType.NOTE, default_orders=[Note.last_modified_at.desc()])

    def convert_filter_to_expression(
        self, filter_: SearchFilterCriteria
    ) -> Expression | None:
        # form_id and form_template_id aren't columns on Note; resolve them
        # through the NoteFormModel join table.
        if filter_.key == "form_id":
            self.add_form_filter(filter_.value)
            return None
        if filter_.key == "form_template_id":
            self.add_form_template_filter(filter_.value)
            return None
        return super().convert_filter_to_expression(filter_)

    def add_title_filter(self, title: str) -> None:
        """Add a filter to search for notes with titles containing the given substring.

        :param title: Substring to search for in note titles.
        :type title: str
        """
        like_pattern = f"%{title}%"
        self.add_expression(Note.title.ilike(like_pattern))

    def add_form_filter(self, form_id: str) -> None:
        """Filter notes that embed the given form via the NoteFormModel join table.

        :param form_id: Id of the Form to filter by.
        :type form_id: str
        """
        # Uncorrelated IN subquery so a note matches at most once, even
        # alongside other filters that add joins.
        self.add_expression(
            Note.id.in_(
                NoteFormModel.select(NoteFormModel.note).where(
                    NoteFormModel.form == form_id
                )
            )
        )

    def add_form_template_filter(self, form_template_id: str) -> None:
        """Filter notes that embed any form bound to the given form template.

        Resolves the template id through NoteFormModel -> Form ->
        FormTemplateVersion via an uncorrelated IN subquery, so a note
        matches at most once regardless of how many embedded forms share
        the template.

        :param form_template_id: Id of the FormTemplate to filter by.
        :type form_template_id: str
        """
        self.add_expression(
            Note.id.in_(
                NoteFormModel.select(NoteFormModel.note)
                .join(Form, on=(Form.id == NoteFormModel.form))
                .join(FormTemplateVersion, on=(FormTemplateVersion.id == Form.template_version))
                .where(FormTemplateVersion.template == form_template_id)
            )
        )
