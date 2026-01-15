import importlib.util

from _doc_assistant_app.app_pages import chat_page, config_page
from gws_streamlit_main import StreamlitMainState, StreamlitRouter

# Initialize GWS - MUST be at the top
StreamlitMainState.initialize()

params = StreamlitMainState.get_params()

router = StreamlitRouter.load_from_session()


def _render_chat_page():
    importlib.reload(chat_page)
    chat_page.render_chat_page(params["prompts_json_path"])


def _render_config_page():
    importlib.reload(config_page)
    config_page.render_config_page(params["prompts_json_path"])


router.add_page(_render_chat_page, title="Chat", url_path="chat", icon="💬")
router.add_page(_render_config_page, title="Config", url_path="config", icon="⚙️")

router.run()
