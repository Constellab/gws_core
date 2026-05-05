from gws_core.impl.rich_text.block.rich_text_block_view import (
    RichTextBlockResourceView,
)
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.model.event.event import Event
from gws_core.model.event.event_listener import EventListener
from gws_core.model.event.event_listener_decorator import event_listener
from gws_core.note.note import Note, NoteScenario
from gws_core.note.note_events import NoteContentUpdatedEvent
from gws_core.note.note_view_model import NoteViewModel
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_dto import TagOriginType
from gws_core.tag.tag_entity_type import TagEntityType


@event_listener
class NoteViewJoinListener(EventListener):
    """Reconcile NoteViewModel rows, view-propagated note tags, and
    note↔scenario associations whenever a Note's content changes.

    Replaces the former NoteService._refresh_note_views_and_tags helper.
    Synchronous so reconciliation runs in the caller's transaction; if
    the listener raises, the surrounding content update rolls back.

    Reads view ids from event.new_content (NOT from the DB) because the
    event dispatches BEFORE the new content is written to note.content.
    """

    def is_synchronous(self) -> bool:
        return True

    def handle(self, event: Event) -> None:
        if not isinstance(event, NoteContentUpdatedEvent):
            return
        _refresh_views_and_tags(event.note_id, event.new_content)


def _refresh_views_and_tags(
    note_id: str, new_content: RichTextDTO | None
) -> None:
    """Diff existing NoteViewModel rows against view ids in new_content;
    insert added rows, delete removed rows, propagate view tags onto the
    note, and bind any view-owning scenarios to the note.
    """
    note = Note.get_by_id(note_id)
    if note is None:
        return

    note_views: list[NoteViewModel] = NoteViewModel.get_by_note(note_id)

    rich_text_views: list[RichTextBlockResourceView] = (
        RichText(new_content).get_resource_views_data()
        if new_content is not None
        else []
    )

    note_tags: EntityTagList = EntityTagList.find_by_entity(
        TagEntityType.NOTE, note_id
    )

    rich_text_view_ids = {
        rich_text_view.view_config_id
        for rich_text_view in rich_text_views
        if rich_text_view.view_config_id is not None
    }

    # Remove view links that disappeared from the content.
    for note_view in note_views:
        if note_view.view.id not in rich_text_view_ids:
            note_view.delete_instance()
            view_tags = EntityTagList.find_by_entity(
                TagEntityType.VIEW, note_view.view.id
            )
            propagated_tags = view_tags.build_tags_propagated(
                TagOriginType.VIEW_PROPAGATED, note_view.view.id
            )
            note_tags.delete_tags(propagated_tags)

    # Add view links for views newly present in the content.
    note_view_ids = {note_view.view.id for note_view in note_views}
    for rich_text_view in rich_text_views:
        if rich_text_view.view_config_id is None:
            continue
        if rich_text_view.view_config_id in note_view_ids:
            continue
        view_config = ViewConfig.get_by_id(rich_text_view.view_config_id)
        if view_config is None:
            continue
        NoteViewModel(note=note, view=view_config).save()
        view_tags = EntityTagList.find_by_entity(
            TagEntityType.VIEW, view_config.id
        )
        propagated_tags = view_tags.build_tags_propagated(
            TagOriginType.VIEW_PROPAGATED, view_config.id
        )
        note_tags.add_tags(propagated_tags)
        note_view_ids.add(view_config.id)

    # Bind any view-owning scenarios that aren't already linked to the note.
    new_note_views: list[NoteViewModel] = NoteViewModel.get_by_note(note_id)
    associated_scenario = NoteScenario.find_scenarios_by_note(note_id)
    for new_view in new_note_views:
        if (
            new_view.view.scenario
            and new_view.view.scenario not in associated_scenario
        ):
            NoteScenario.create_obj(new_view.view.scenario, note).save()
            associated_scenario.append(new_view.view.scenario)
