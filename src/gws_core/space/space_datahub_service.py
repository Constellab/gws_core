

from typing import Optional

from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException
from gws_core.space.space_dto import SpaceDocumentDTO
from gws_core.space.space_service_base import SpaceServiceBase

from ..core.service.external_api_service import ExternalApiService


class SpaceDatahubService(SpaceServiceBase):

    # external datahub route on space
    _EXTERNAL_DATAHUB_ROUTE: str = 'external-datahub'

    def get_object_url_from_filename(self, filename: str) -> Optional[str]:
        """Get the object url from filename."""
        return self._get_space_api_url(
            f"{self._EXTERNAL_DATAHUB_ROUTE}/document/redirect/{filename}")
