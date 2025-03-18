

import importlib.util

import streamlit as st

from gws_core.impl.apps.doc_assistant._doc_assistant_app.pages import \
    doc_assistant_product_page

sources: list
params: dict


def _render_doc_product_page():
    importlib.reload(doc_assistant_product_page)
    doc_assistant_product_page.render_product_assistant_page(params['product_doc_default_prompt'])


product_page = st.Page(_render_doc_product_page, title='Product documentation',
                       url_path='product-doc', icon='🚀')

pg = st.navigation([product_page])

pg.run()
