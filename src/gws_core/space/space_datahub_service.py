
from gws_core.space.space_service_base import SpaceServiceBase


class SpaceDatahubService(SpaceServiceBase):
    # external datahub route on space
    _EXTERNAL_DATAHUB_ROUTE: str = "external-datahub"

    def get_object_url_from_filename(self, filename: str) -> str | None:
        """Get the object url from filename."""
        return self._get_space_api_url(
            f"{self._EXTERNAL_DATAHUB_ROUTE}/document/redirect/{filename}"
        )
