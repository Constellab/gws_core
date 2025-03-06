
from gws_core import LabNoteResource
from gws_core.streamlit import StreamlitContainer, rich_text_editor


def render_getting_started_page(note: LabNoteResource):

    with StreamlitContainer.container_centered('note-container'):
        rich_text_editor(initial_value=note.get_content(), disabled=True)
