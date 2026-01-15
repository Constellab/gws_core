"""Streamlit module for virtual-env apps.
Can be imported as: from gws_streamlit_env_main import register_gws_streamlit_env_app
"""

# Re-export everything from base
from gws_streamlit_base import *

# Env-specific exports
from .gws_streamlit_env_main_state import StreamlitEnvMainState as StreamlitEnvMainState

__all__ = [
    "StreamlitEnvMainState",
]
