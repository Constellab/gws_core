

import importlib.util

from _doc_assistant_app.pages import chat_page, config_page

from gws_core.streamlit import StreamlitRouter

sources: list
params: dict

router = StreamlitRouter.load_from_session()


def _render_chat_page():
    importlib.reload(chat_page)
    chat_page.render_chat_page(params['prompts_json_path'])


def _render_config_page():
    importlib.reload(config_page)
    config_page.render_config_page(params['prompts_json_path'])


router.add_page(_render_chat_page, title='Chat', url_path='chat', icon='💬')
router.add_page(_render_config_page, title='Config', url_path='config', icon='⚙️')

router.run()
