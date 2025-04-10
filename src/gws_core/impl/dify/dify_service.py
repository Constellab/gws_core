import json
import os
from typing import Any, Dict, Generator, List, Literal, Optional, Union

import requests
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.service.external_api_service import (ExternalApiService,
                                                        FormData)
from gws_core.credentials.credentials_type import CredentialsDataOther

DifyIndexingTechnique = Literal['economic', 'high_quality']


class DifySendDocumentOptions(BaseModelDTO):
    indexing_technique: DifyIndexingTechnique = 'economic'
    remove_extra_spaces: bool = True
    remove_urls_emails: bool = False
    chunk_separator: str = '\n\n'
    chunk_max_tokens: int = 500
    lang: Optional[str] = None


class DifySendMessageSource(BaseModelDTO):
    dataset_id: str
    dataset_name: str
    document_id: str
    document_name: str
    data_source_type: Literal['upload_file']
    retriever_from: Literal['api']
    score: float  # 0-1


class DifySendMessageStreamResponse(BaseModelDTO):
    answer: str


class DifySendEndMessageStreamResponse(BaseModelDTO):
    conversation_id: Optional[str] = None
    sources: Optional[List[DifySendMessageSource]] = None


class DifyService:
    """Service to interact with Dify API"""

    route: str
    api_key: str

    def __init__(self, route: str, api_key: str):
        self.route = route
        self.api_key = api_key

    def send_document(self, doc_path: str, dataset_id: str,
                      options: DifySendDocumentOptions) -> dict:

        route = f'{self.route}/datasets/{dataset_id}/document/create-by-file'

        body = {
            "indexing_technique": options.indexing_technique,
            "doc_language": options.lang,
            "process_rule": {
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
        }

        headers = {
            'Authorization': 'Bearer ' + self.api_key,
        }

        form_data = FormData()
        form_data.add_file_from_path('file', doc_path)
        form_data.add_json_data('data', body)

        response = ExternalApiService.post_form_data(
            route,
            form_data=form_data,
            headers=headers,
            timeout=10,
            raise_exception_if_error=True
        )

        return response.json()

    def send_message_stream(self, query: str, conversation_id: Optional[str] = None,
                            user: Optional[str] = None,
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
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "query": query,
            "response_mode": "streaming",
            "inputs": inputs or {}
        }

        if conversation_id:
            data["conversation_id"] = conversation_id

        if user:
            data["user"] = user

        if files:
            data["files"] = files

        dify_response = DifySendEndMessageStreamResponse(
            conversation_id=None,
            sources=[]
        )

        try:
            with requests.post(url, headers=headers, json=data, stream=True) as response:
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

    @staticmethod
    def from_credentials(credentials: CredentialsDataOther):
        # check credentials
        if 'route' not in credentials.data:
            raise ValueError("The credentials must contain the field 'route'")
        if 'api_key' not in credentials.data:
            raise ValueError("The credentials must contain the field 'api_key'")
        return DifyService(credentials.data['route'], credentials.data['api_key'])
