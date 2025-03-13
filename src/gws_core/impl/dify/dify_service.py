from typing import Literal

from gws_core.core.service.external_api_service import (ExternalApiService,
                                                        FormData)
from gws_core.credentials.credentials_type import CredentialsDataOther

DifyIndexingTechnique = Literal['economic', 'high_quality']


class DifyService:
    """Service to interact with Dify API"""

    route: str
    api_key: str

    def __init__(self, route: str, api_key: str):
        self.route = route
        self.api_key = api_key

    def send_document(self, doc_path: str, dataset_id: str,
                      indexing_technique: DifyIndexingTechnique,
                      lang: str = None) -> dict:

        route = f'{self.route}/datasets/{dataset_id}/document/create-by-file'

        body = {
            'indexing_technique': indexing_technique,
            "process_rule": {"mode": "automatic"},
            'doc_language': lang
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
