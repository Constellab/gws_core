
from gws_core import LabNoteResource
from gws_core.streamlit import StreamlitContainers, rich_text_editor


def render_getting_started_page(note: LabNoteResource):

    with StreamlitContainers.container_centered('note-container'):
        rich_text_editor(initial_value=note.get_content(), disabled=False)
