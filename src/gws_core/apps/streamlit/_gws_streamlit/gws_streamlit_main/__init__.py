"""Main Streamlit module for non-virtual-env apps (with gws_core access).
Can be imported as: from gws_streamlit_main import StreamlitAppState
"""

# Re-export everything from base
from gws_streamlit_base import *

# Components
from .components.streamlit_class_doc_component import class_doc_component as class_doc_component
from .components.streamlit_doc_component import method_doc_component as method_doc_component
from .components.streamlit_doc_component import render_method_doc as render_method_doc
from .components.streamlit_open_ai_chat import StreamlitOpenAiChat as StreamlitOpenAiChat
from .components.streamlit_resource_search_input import ResourceSearchInput as ResourceSearchInput
from .gws_components.streamlit_menu_button import StreamlitMenuButton as StreamlitMenuButton
from .gws_components.streamlit_menu_button import StreamlitMenuButtonItem as StreamlitMenuButtonItem
from .gws_components.streamlit_resource_select import (
    StreamlitResourceSelect as StreamlitResourceSelect,
)

# GWS Components
from .gws_components.streamlit_rich_text_component import rich_text_editor as rich_text_editor
from .gws_components.streamlit_task_runner import StreamlitTaskRunner as StreamlitTaskRunner
from .gws_components.streamlit_tree_menu import StreamlitTreeMenu as StreamlitTreeMenu
from .gws_components.streamlit_tree_menu import StreamlitTreeMenuItem as StreamlitTreeMenuItem

# State Management
from .gws_streamlit_main_state import StreamlitMainState as StreamlitMainState
from .gws_streamlit_main_state import StreamlitUserAuthInfo as StreamlitUserAuthInfo
