
import importlib

from datahub_dify_app_state import DatahubDifyAppState
from pages import datahub_dify_app_chat_page, datahub_dify_app_config_page

from gws_core.impl.apps.datahub_dify_app._datahub_dify_app.datahub_dify_app_expert_state import \
    DatahubDifyAppExpertState
from gws_core.impl.dify import doc_expert_ai_page
from gws_core.impl.dify.dify_service import DifyService
from gws_core.impl.dify.doc_expert_ai_page_state import DocExpertAIPageConfig
from gws_core.streamlit import StreamlitRouter

sources: list
params: dict

# Uncomment if you want to hide the Streamlit sidebar toggle and always show the sidebar
# from gws_core.streamlit import StreamlitHelper
# StreamlitHelper.hide_sidebar_toggle()

router = StreamlitRouter.load_from_session()

# Initialize the app state
DatahubDifyAppState.init(
    chat_credentials_name=params.get('chat_credentials_name'),
    knowledge_base_credentials_name=params.get('knowledge_base_credentials_name'),
    knowledge_base_id=params.get('knowledge_base_id')
)

expert_config = DocExpertAIPageConfig.get_default_config(params.get('knowledge_base_id'))
dify_service = DifyService.from_credentials(DatahubDifyAppState.get_knowledge_base_credentials())
expert_state = DatahubDifyAppExpertState.init(expert_config, dify_service)


def _render_chat_page():
    importlib.reload(datahub_dify_app_chat_page)
    datahub_dify_app_chat_page.render_page()


def _render_expert_ai_page():
    importlib.reload(doc_expert_ai_page)
    doc_expert_ai_page.render_doc_expert_ai_page(expert_state)


def _render_config_page():
    importlib.reload(datahub_dify_app_config_page)
    datahub_dify_app_config_page.render_page()


router.add_page(_render_chat_page, title='Chat page', url_path='chat-page', icon='💬')
router.add_page(_render_expert_ai_page, title='Expert AI page', url_path=expert_config.page_url, icon='🤖')
router.add_page(_render_config_page, title='Config page', url_path='config-page', icon='⚙️')

router.run()
