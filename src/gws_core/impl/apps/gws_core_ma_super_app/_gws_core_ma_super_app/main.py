

import streamlit as st

from _gws_core_ma_super_app.pages import first_page

sources: list
params: dict

# Uncomment if you want to hide the Streamlit sidebar toggle and always show the sidebar
# from gws_core.streamlit import StreamlitHelper
# StreamlitHelper.hide_sidebar_toggle()


def _render_first_page():
    first_page.render_first_page()


_first_page = st.Page(_render_first_page, title='First page', url_path='first-page', icon='📦')
pg = st.navigation([_first_page])

pg.run()
