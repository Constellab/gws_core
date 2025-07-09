

import importlib.util

import streamlit as st
from _doc_assistant_app.pages import doc_assistant_page

sources: list
params: dict


def _render_product_doc_page():
    importlib.reload(doc_assistant_page)
    doc_assistant_page.render_assistant_page(
        'product',
        params['product_doc_default_prompt'],
        'Product documentation assistant',
        'This assistant helps you to generate the product documentation of Constellab.')


def _render_technical_doc_page():
    importlib.reload(doc_assistant_page)
    doc_assistant_page.render_assistant_page(
        'technical',
        params['technical_doc_default_prompt'],
        'Technical documentation assistant',
        'This assistant helps you to generate the technical documentation of Constellab.')


product_page = st.Page(_render_product_doc_page, title='Product documentation',
                       url_path='product-doc', icon='🚀')
technical_page = st.Page(_render_technical_doc_page, title='Technical documentation',
                         url_path='technical-doc', icon='🛠️')

pg = st.navigation([product_page, technical_page])

pg.run()
