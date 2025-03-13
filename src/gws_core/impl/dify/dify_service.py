from typing import Literal, Optional

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

    @staticmethod
    def from_credentials(credentials: CredentialsDataOther):
        # check credentials
        if 'route' not in credentials.data:
            raise ValueError("The credentials must contain the field 'route'")
        if 'api_key' not in credentials.data:
            raise ValueError("The credentials must contain the field 'api_key'")
        return DifyService(credentials.data['route'], credentials.data['api_key'])
