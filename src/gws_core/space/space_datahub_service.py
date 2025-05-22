

from typing import Optional

from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException
from gws_core.space.space_dto import SpaceDocumentDTO
from gws_core.space.space_service_base import SpaceServiceBase

from ..core.service.external_api_service import ExternalApiService


class SpaceDatahubService(SpaceServiceBase):

    # external datahub route on space
    _EXTERNAL_DATAHUB_ROUTE: str = 'external-datahub'

    def find_document_by_filename(self, filename: str) -> Optional[SpaceDocumentDTO]:
        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_DATAHUB_ROUTE}/document/filename/{filename}")

        try:
            response = ExternalApiService.get(space_api_url, self._get_request_header(),
                                              raise_exception_if_error=True)
            return SpaceDocumentDTO.from_json(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't find document by filename in space. Error : {err.detail}"
            raise err

    def get_object_url_from_filename(self, filename: str) -> Optional[str]:
        """Get the object url from filename."""
        return self._get_space_api_url(
            f"{self._EXTERNAL_DATAHUB_ROUTE}/document/filename/{filename}")
