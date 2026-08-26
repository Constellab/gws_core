from gws_streamlit_env_main import StreamlitEnvMainState, StreamlitRouter

from {{folderAppName}}.app_pages import first_page, second_page

sources: list
params: dict

# Uncomment if you want to hide the Streamlit sidebar toggle and always show the sidebar
# from gws_core.streamlit import StreamlitHelper
# StreamlitHelper.hide_sidebar_toggle()
# Initialize GWS - MUST be at the top
# This app runs in a virtual environment and cannot load gws_core.
# The env state exposes the input resources as file paths.
StreamlitEnvMainState.initialize()

router = StreamlitRouter.load_from_session()


def _render_first_page():
    first_page.render_first_page()


def _render_second_page():
    second_page.render_second_page()


router.add_page(_render_first_page, title="First page", url_path="first-page", icon="📦")
router.add_page(_render_second_page, title="Second page", url_path="second-page", icon="📦")
router.run()
