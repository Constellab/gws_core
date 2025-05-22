import json
from typing import Any, Dict, Generator, List, Literal, Optional, Union

import requests

from gws_core.core.service.external_api_service import (ExternalApiService,
                                                        FormData)
from gws_core.core.utils.logger import Logger
from gws_core.credentials.credentials_type import CredentialsDataOther
from gws_core.impl.dify.dify_class import (
    DifyChunksResponse, DifyCreateDatasetMetadataRequest,
    DifyCreateDatasetMetadataResponse, DifyDocumentChunksResponse,
    DifyGetDatasetMetadataResponse, DifyGetDatasetMetadataResponseMetadata,
    DifySendDocumentOptions, DifySendDocumentResponse,
    DifySendEndMessageStreamResponse, DifySendMessageSource,
    DifySendMessageStreamResponse, DifyUpdateDocumentOptions,
    DifyUpdateDocumentsMetadataRequest, DifyUploadFile, DifyUploadFileResponse)


class DifyService:
    """Service to interact with Dify API"""

    route: str
    api_key: str

    def __init__(self, route: str, api_key: str):
        self.route = route
        self.api_key = api_key

    def send_document(self, doc_path: str, dataset_id: str,
                      options: DifySendDocumentOptions, filename: str = None) -> DifySendDocumentResponse:

        route = f'{self.route}/datasets/{dataset_id}/document/create-by-file'

        body = {
            "indexing_technique": options.indexing_technique,
            "doc_language": options.lang,
            "process_rule": self._get_process_rule(options),
        }

        form_data = FormData()
        form_data.add_file_from_path('file', doc_path, filename)
        form_data.add_json_data('data', body)

        response = ExternalApiService.post_form_data(
            route,
            form_data=form_data,
            headers=self._get_http_headers(),
            timeout=10,
            raise_exception_if_error=True
        )

        return DifySendDocumentResponse.from_json(response.json())

    def update_document(self, doc_path: str, dataset_id: str, document_id: str,
                        options: DifySendDocumentOptions, filename: str = None) -> DifySendDocumentResponse:
        """Update a document in a dataset.
        Parameters
        ----------
        doc_path : str
            Path to the document file
        dataset_id : str
            Knowledge Base ID
        document_id : str
            Document ID to update
        options : DifyUpdateDocumentOptions
            Options for updating the document
        Returns
        -------
        DifySendDocumentResponse
            Response containing the updated document information
        Raises
        ------
        requests.exceptions.HTTPError
            If the API request fails
        """
        route = f'{self.route}/datasets/{dataset_id}/documents/{document_id}/update-by-file'
        body = {
            "process_rule": self._get_process_rule(options),
        }

        form_data = FormData()
        form_data.add_file_from_path('file', doc_path, filename)
        form_data.add_json_data('data', body)
        response = ExternalApiService.post_form_data(
            route,
            form_data=form_data,
            headers=self._get_http_headers(),
            timeout=10,
            raise_exception_if_error=True
        )
        return DifySendDocumentResponse.from_json(response.json())

    def _get_process_rule(self, options: DifyUpdateDocumentOptions) -> Dict[str, Any]:
        """Get the process rule for document update."""
        return {
            "rules": {
                "pre_processing_rules": [
                    {"id": "remove_extra_spaces", "enabled": options.remove_extra_spaces},
                    {"id": "remove_urls_emails", "enabled": options.remove_urls_emails}
                ],
                "segmentation": {
                    "separator": options.chunk_separator,
                    "max_tokens": options.chunk_max_tokens
                }
            },
            "mode": "custom"
        }

    def search_chunks(self, dataset_id: str, query: str,
                      search_method: Literal['keyword_search', 'semantic_search', 'full_text_search', 'hybrid_search'] = 'semantic_search',
                      reranking_enable: bool = False,
                      reranking_provider_name: Optional[str] = None,
                      reranking_model_name: Optional[str] = None,
                      weights: Optional[float] = None,
                      top_k: Optional[int] = 5,
                      score_threshold_enabled: bool = False,
                      score_threshold: Optional[float] = 0) -> DifyChunksResponse:
        """Retrieve chunks from a Knowledge Base (dataset).

        This method retrieves relevant chunks from the specified dataset based on the query
        and search parameters.

        Parameters
        ----------
        dataset_id : str
            Knowledge Base ID
        query : str
            Query keyword to search for
        search_method : Literal['keyword_search', 'semantic_search', 'full_text_search', 'hybrid_search'], optional
            Search method to use, by default 'semantic_search'
        reranking_enable : bool, optional
            Whether to enable reranking, by default False
        reranking_provider_name : Optional[str], optional
            Rerank model provider, required if reranking is enabled
        reranking_model_name : Optional[str], optional
            Rerank model name, required if reranking is enabled
        weights : Optional[float], optional
            Semantic search weight setting in hybrid search mode
        top_k : Optional[int], optional
            Number of results to return
        score_threshold_enabled : bool, optional
            Whether to enable score threshold, by default False
        score_threshold : Optional[float], optional
            Score threshold value, used if score_threshold_enabled is True

        Returns
        -------
        DifyChunksResponse
            Response containing query info and retrieved chunks

        Raises
        ------
        requests.exceptions.HTTPError
            If the API request fails
        """
        route = f'{self.route}/datasets/{dataset_id}/retrieve'

        # Prepare retrieval model configuration
        retrieval_model = {
            "search_method": search_method,
            "top_k": top_k,
            "score_threshold_enabled": score_threshold_enabled,
            "score_threshold": score_threshold
        }

        # Add reranking configuration if enabled
        if reranking_enable:
            retrieval_model["reranking_enable"] = True
            if reranking_provider_name and reranking_model_name:
                retrieval_model["reranking_mode"] = {
                    "reranking_provider_name": reranking_provider_name,
                    "reranking_model_name": reranking_model_name
                }
        else:
            retrieval_model["reranking_enable"] = False

        # Add weights for hybrid search if specified
        if search_method == "hybrid_search" and weights is not None:
            retrieval_model["weights"] = weights

        # Prepare request body
        body = {
            "query": query,
            "retrieval_model": retrieval_model,
        }

        response = requests.post(
            route,
            json=body,
            headers=self._get_http_headers(content_type=True),
            timeout=10
        )

        response.raise_for_status()
        response_data = response.json()
        return DifyChunksResponse.from_json(response_data)

    def get_document_chunks(self, dataset_id: str, document_id: str,
                            keyword: Optional[str] = None,
                            status: str = "completed",
                            page: int = 1,
                            limit: int = 20) -> DifyDocumentChunksResponse:
        """Get chunks from a specific document in a knowledge base.

        This method retrieves chunks from a specific document within a dataset.

        Parameters
        ----------
        dataset_id : str
            Knowledge Base ID
        document_id : str
            Document ID to get chunks from
        keyword : Optional[str], optional
            Search keyword to filter chunks, by default None
        status : str, optional
            Search status filter, by default "completed"
        page : int, optional
            Page number for pagination, by default 1
        limit : int, optional
            Number of items to return per page (1-100), by default 20

        Returns
        -------
        DifyDocumentChunksResponse
            Response containing the document chunks and pagination info

        Raises
        ------
        requests.exceptions.HTTPError
            If the API request fails
        """
        route = f'{self.route}/datasets/{dataset_id}/documents/{document_id}/segments'

        # Build query parameters
        params = {
            'status': status,
            'page': page,
            'limit': limit
        }

        # Add optional keyword parameter if provided
        if keyword:
            params['keyword'] = keyword

        response = requests.get(
            route,
            params=params,
            headers=self._get_http_headers(),
            timeout=10
        )

        response.raise_for_status()
        response_data = response.json()
        return DifyDocumentChunksResponse.from_json(response_data)

    def get_document_file(
            self, dataset_id: str, document_id: str) -> DifyUploadFileResponse:
        """Get information about a document's uploaded file and optionally download it.

        This method retrieves information about the uploaded file associated with a document
        and can optionally download the file to a temporary directory.

        Parameters
        ----------
        dataset_id : str
            Knowledge Base ID
        document_id : str
            Document ID to get the file information for
        download_to_temp : bool, optional
            Whether to download the file to a temporary directory, by default True

        Returns
        -------
        Download url

        Raises
        ------
        requests.exceptions.HTTPError
            If the API request fails
        RuntimeError
            If file download fails
        """

        # First get the file information
        route = f'{self.route}/datasets/{dataset_id}/documents/{document_id}/upload-file'

        # Get file information
        response = requests.get(
            route,
            headers=self._get_http_headers(),
            timeout=10
        )

        response.raise_for_status()
        response_data = response.json()
        file_info = DifyUploadFile.from_json(response_data)

        return DifyUploadFileResponse(
            file=file_info,
            base_dify_url=self.get_base_url()
        )

    def delete_document(self, dataset_id: str, document_id: str) -> None:
        """Delete a document from a dataset.

        Parameters
        ----------
        dataset_id : str
            Knowledge Base ID
        document_id : str
            Document ID to delete

        Raises
        ------
        requests.exceptions.HTTPError
            If the API request fails
        """
        route = f'{self.route}/datasets/{dataset_id}/documents/{document_id}'

        response = requests.delete(
            route,
            headers=self._get_http_headers(),
            timeout=10
        )

        response.raise_for_status()

    ################################# CHAT #################################

    def send_message_stream(self, query: str,
                            user: str,
                            conversation_id: Optional[str] = None,
                            inputs: Optional[Dict[str, Any]] = None,
                            files: Optional[list] = None) -> Generator[Union[str, DifySendMessageStreamResponse, DifySendEndMessageStreamResponse], None, None]:
        """
        Call the Dify API chat endpoint with streaming response.

        Args:
            query: The user's message
            conversation_id: Optional ID for continuing a conversation
            user: Optional user identifier
            inputs: Optional dictionary of input variables
            files: Optional list of files to include

        Returns:
            Generator that yields response chunks (string or objects)
        """
        url = f"{self.route}/chat-messages"

        data = {
            "query": query,
            "response_mode": "streaming",
            "inputs": inputs or {},
            "user": user,
        }

        if conversation_id:
            data["conversation_id"] = conversation_id

        if files:
            data["files"] = files

        dify_response = DifySendEndMessageStreamResponse(
            conversation_id=None,
            sources=[]
        )

        try:
            with requests.post(url, headers=self._get_http_headers(content_type=True),
                               json=data, stream=True, timeout=30) as response:
                response.raise_for_status()
                buffer = ""

                for chunk in response.iter_content(chunk_size=1):
                    if chunk:
                        chunk_str = chunk.decode('utf-8')
                        buffer += chunk_str

                        if buffer.endswith('\n') and buffer.strip():
                            try:
                                line = buffer.strip()
                                if line.startswith('data: '):
                                    line = line[6:]  # Remove 'data: ' prefix
                                    if line == '[DONE]':
                                        break

                                    json_data = json.loads(line)
                                    if 'event' in json_data and json_data['event'] == 'message':
                                        # Update conversation_id in response object
                                        if 'conversation_id' in json_data:
                                            dify_response.conversation_id = json_data['conversation_id']

                                        # Yield message response for streaming text
                                        if 'answer' in json_data:
                                            message_response = DifySendMessageStreamResponse(
                                                answer=json_data['answer']
                                            )
                                            yield message_response

                                    if 'event' in json_data and json_data['event'] == 'message_end':
                                        # Update conversation_id in final response
                                        if 'conversation_id' in json_data:
                                            dify_response.conversation_id = json_data['conversation_id']

                                        # Process sources if available
                                        if 'metadata' in json_data and 'retriever_resources' in json_data['metadata']:
                                            for source in json_data['metadata']['retriever_resources']:
                                                dify_response.sources.append(DifySendMessageSource(
                                                    dataset_id=source['dataset_id'],
                                                    dataset_name=source['dataset_name'],
                                                    document_id=source['document_id'],
                                                    document_name=source['document_name'],
                                                    data_source_type='upload_file',
                                                    retriever_from='api',
                                                    score=source['score']
                                                ))

                                        # Yield final response with metadata
                                        yield dify_response
                            except json.JSONDecodeError:
                                pass
                            buffer = ""

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error calling Dify API: {str(e)}") from e

    ################################### METADATA ###################################

    def create_dataset_metadata(
            self, dataset_id: str, metadata: DifyCreateDatasetMetadataRequest) -> DifyCreateDatasetMetadataResponse:
        """Create metadata for a specific document in a dataset.
        Parameters
        ----------
        dataset_id : str
            Knowledge Base ID
        body : DifyCreateMetadataRequest
            Metadata to create
        Raises
        ------
        requests.exceptions.HTTPError
            If the API request fails
        """
        route = f'{self.route}/datasets/{dataset_id}/metadata'
        response = requests.post(
            route,
            json=metadata.to_json_dict(),
            headers=self._get_http_headers(),
            timeout=30
        )
        response.raise_for_status()
        return DifyCreateDatasetMetadataResponse.from_json(response.json())

    def get_dataset_all_metadata(
            self, dataset_id: str) -> DifyGetDatasetMetadataResponse:
        """Get metadata for a specific dataset.
        Parameters
        ----------
        dataset_id : str
            Knowledge Base ID
        Raises
        ------
        requests.exceptions.HTTPError
            If the API request fails
        """
        route = f'{self.route}/datasets/{dataset_id}/metadata'
        response = requests.get(
            route,
            headers=self._get_http_headers(),
            timeout=30
        )
        response.raise_for_status()
        return DifyGetDatasetMetadataResponse.from_json(response.json())

    def get_dataset_metadata(
            self, dataset_id: str, metadata_name: str) -> DifyGetDatasetMetadataResponseMetadata | None:
        """Get metadata for a specific dataset.
        Parameters
        ----------
        dataset_id : str
            Knowledge Base ID
        metadata_name : str
            Metadata name to get
        Raises
        ------
        requests.exceptions.HTTPError
            If the API request fails
        """

        metadata = self.get_dataset_all_metadata(dataset_id)

        for meta in metadata.doc_metadata:
            if meta.name == metadata_name:
                return meta

        return None

    def get_or_create_dataset_metadata(
            self, dataset_id: str, metadata: DifyCreateDatasetMetadataRequest) -> DifyGetDatasetMetadataResponseMetadata:
        """Get or create the access right metadata in Dify."""
        dify_metadata = self.get_dataset_metadata(dataset_id, metadata.name)

        if dify_metadata is not None:
            return dify_metadata

        Logger.info(f"The {metadata.name} metadata does not exist in dify. Creating it.")

        self.create_dataset_metadata(dataset_id, metadata)

        dify_metadata = self.get_dataset_metadata(dataset_id, metadata.name)
        if dify_metadata is None:
            raise ValueError(f"The {metadata.name} metadata could not be created in dify in dataset : {dataset_id}.")
        return dify_metadata

    def update_document_metadata(
            self, dataset_id: str, body: List[DifyUpdateDocumentsMetadataRequest]) -> None:
        """Update metadata for a specific document in a dataset.

        Parameters
        ----------
        dataset_id : str
            Knowledge Base ID
        document_id : str
            Document ID to update metadata for
        metadata : Dict[str, Any]
            Metadata to update

        Raises
        ------
        requests.exceptions.HTTPError
            If the API request fails
        """
        route = f'{self.route}/datasets/{dataset_id}/documents/metadata'

        response = requests.post(
            route,
            json={"operation_data": DifyUpdateDocumentsMetadataRequest.to_json_list(body)},
            headers=self._get_http_headers(content_type=True),
            timeout=30
        )

        response.raise_for_status()

    def _get_http_headers(self, content_type: bool = False) -> Dict[str, str]:
        """Get the HTTP headers for the Dify API requests.

        Returns:
            Dict[str, str]: HTTP headers
        """
        headers = {
            'Authorization': 'Bearer ' + self.api_key,
        }
        if content_type:
            headers['Content-Type'] = 'application/json'
        return headers

    def get_base_url(self) -> str:
        """Get the base URL of the Dify API before the first '/'.
        Returns:
            str: Base URL of the Dify API
        """
        return self.route.split('/')[0] + '//' + self.route.split('/')[2]

    @staticmethod
    def from_credentials(credentials: CredentialsDataOther):
        # check credentials
        if 'route' not in credentials.data:
            raise ValueError("The credentials must contain the field 'route'")
        if 'api_key' not in credentials.data:
            raise ValueError("The credentials must contain the field 'api_key'")
        return DifyService(credentials.data['route'], credentials.data['api_key'])
