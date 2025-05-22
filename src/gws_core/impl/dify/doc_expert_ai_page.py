
import streamlit as st

from gws_core.impl.dify.doc_expert_ai_page_state import (
    DocAiExpertDifyDocument, DocAiExpertPageState, DocExpertSelectedDocument)
from gws_core.impl.openai.open_ai_chat import OpenAiChat
from gws_core.streamlit import StreamlitContainers


def render_doc_expert_ai_page(state: DocAiExpertPageState):
    """
    Render the article AI page.
    """
    with StreamlitContainers.container_centered(key='article-ai-page'):
        col1, col2 = StreamlitContainers.columns_with_fit_content(key='article-header',
                                                                  cols=[1, 'fit-content'],
                                                                  vertical_align_items='center')
        with col1:
            st.title(state.config.page_emoji + " " + state.config.page_name)

        with col2:
            # reset button
            if st.button("Reset"):
                state.reset()

        status = state.get_status()
        if status == 'SEARCH':
            # Render the query form
            _render_query_form(state)
        elif status == "SEARCH_RESULTS":
            # Display search results
            _render_search_results(state)
        elif status == "DOCUMENT_CHAT":
            # Display document chat
            _render_document_chat(state)
        elif status == "DOCUMENT_SELECTED_NOT_LOADED":
            _load_chunks(state)


def _render_query_form(state: DocAiExpertPageState):
    with st.expander('Configuration'):
        dataset_id = st.text_input(
            "Knowledge Base ID",
            value=state.config.default_dataset_id,
            help="Enter the knowledge base ID for the article AI"
        )
        if dataset_id:
            # Store dataset ID in state
            state.set_default_dataset_id(dataset_id)

        query_weight = st.slider(
            "Semantic weight",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Set the query weight for the search"
        )
        if query_weight:
            # Store query weight in state
            state.set_query_weight(query_weight)

    query = st.text_input(
        "Query",
        value="",
        help="Enter a query for the article AI"
    )

    if st.button("Search"):
        if not query:
            st.error("Please enter a query")
            return

        # Store query in state
        state.set_query(query)

        with st.spinner("Searching in documents..."):
            # if st.button("Get Answer"):
            result = state.dify_service.search_chunks(
                state.get_default_dataset_id(),
                weights=state.get_query_weight(),
                query=query,
                search_method='hybrid_search',
                top_k=5,
                score_threshold=0,
                reranking_enable=False, score_threshold_enabled=False)
            if result:
                # Store search results in state
                state.set_documents_result(result)
                st.rerun()
            else:
                st.error("No results found")
                return


def _render_search_results(state: DocAiExpertPageState):
    # Display search results
    st.subheader(f"Search Results for '{state.get_query()}'")
    result = state.get_documents_result()

    docs = result.get_distinct_documents()
    if docs:
        st.write(f"**Found {len(docs)} documents. Please select a document**")
        for doc in docs:
            col1, col2, col3 = st.columns([3, 1, 1])
            dify_document = DocAiExpertDifyDocument(
                id=doc.id,
                name=doc.name,
                dataset_id=state.get_default_dataset_id()
            )
            with col1:
                if st.button(doc.name, key=f"view_{doc.id}"):
                    # Store selected document in state
                    state.set_selected_document(dify_document)
                    _load_chunks(state)
            with col2:
                if st.button("Download", key=f"download_{doc.id}"):
                    _download_document(state, dify_document)
            with col3:
                st.text("")  # Empty space for alignment
    else:
        st.info("No documents found")


def _load_chunks(state: DocAiExpertPageState):

    chunks_response = None
    # Display document chunks
    with st.spinner("Loading document chunks..."):
        try:
            selected_document = state.get_selected_document()
            chunks_response = state.dify_service.get_document_chunks(
                dataset_id=selected_document.dataset_id,
                document_id=selected_document.id,
                limit=30
            )

            if not chunks_response:
                raise Exception("No chunks found for the selected document")
        except Exception as e:
            st.error(f"Error fetching document chunks: {str(e)}")

    summary: str = _summarize_document(state, chunks_response.get_all_chunk_texts())

    selected_document = DocExpertSelectedDocument(
        chunks_response=chunks_response,
        summary=summary
    )

    # Store selected document in state
    state.set_selected_document_chunks(selected_document)
    st.rerun()


def _summarize_document(state: DocAiExpertPageState, document_content: str):
    # summarize the document
    summary_prompt = state.config.summary_prompt

    if not summary_prompt:
        return None

    if "[DOC_CONTENT]" not in summary_prompt:
        raise Exception(
            'The summary prompt must contain the [DOC_CONTENT] placeholder in the expert page configuration')

    with st.spinner("Summarizing document..."):

        # Replace the [DOC_CONTENT] placeholder with the document content
        summary_prompt = summary_prompt.replace(
            "[DOC_CONTENT]", document_content)

        chat = OpenAiChat()
        chat.add_user_message(summary_prompt)
        return chat.call_gpt()


def _render_document_chat(state: DocAiExpertPageState):

    # Display document chat
    selected_document = state.get_selected_document()
    st.subheader(f"📄 {selected_document.name}")

    # Get chunks
    doc_chunk = state.get_selected_document_chunks()

    system_prompt = state.config.system_prompt

    if "[DOC_CONTENT]" not in system_prompt:
        raise Exception('The system prompt must contain the [DOC_CONTENT] placeholder in the expert page configuration')

    # Replace the [DOC_CONTENT] placeholder with the document content
    system_prompt = system_prompt.replace(
        "[DOC_CONTENT]", doc_chunk.chunks_response.get_all_chunk_texts())

    streamlit_ai_chat = state.load_chat(system_prompt=system_prompt)

    with StreamlitContainers.row_container(key='document-action'):

        document_url = state.get_document_url(selected_document.id)
        if document_url:
            st.link_button('View document', document_url,
                           icon=':material/open_in_new:')

        if st.button("Download document", icon=':material/download:', key=f"download_{selected_document.id}"):
            _download_document(state, selected_document)

        if st.button("New chat", icon=':material/replay:', key='new_chat'):
            streamlit_ai_chat.reset()

    # Render the document resume
    if doc_chunk.summary:
        st.markdown('### 💡Document Summary')
        st.markdown(doc_chunk.summary)

    st.divider()
    st.markdown('### 💬 Expert chat')

    # Display the chat messages
    streamlit_ai_chat.show_chat()

    if streamlit_ai_chat.last_message_is_user():
        with st.spinner('Processing...'):
            streamlit_ai_chat.call_gpt()

            # re-run the app
            st.rerun()

    user_prompt = st.chat_input(
        f"Ask a question about the document {selected_document.name}")

    if user_prompt:
        # add the message and rerun the app, so the message is shown before call to GPT
        streamlit_ai_chat.add_user_message(user_prompt)

        # re-run the app
        st.rerun()


def _download_document(state: DocAiExpertPageState, document: DocAiExpertDifyDocument):
    """
    Download a document and provide a download link.

    Args:
        document_id: ID of the document to download
        dify_service: DifyService instance
    """
    with st.spinner("Preparing download for document..."):
        try:

            download_file = state.dify_service.get_document_file(
                dataset_id=document.dataset_id,
                document_id=document.id,
            )

            # Make a download link
            st.markdown(
                f'<a href="{download_file.get_download_url()}" download="{download_file.file.name}">Click to download document</a>',
                unsafe_allow_html=True
            )

        except Exception as e:
            st.error(f"Error downloading document: {str(e)}")
