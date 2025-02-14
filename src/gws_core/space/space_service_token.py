

from typing import Dict

from gws_core.space.space_service import SpaceService


class SpaceServiceToken(SpaceService):
    """
    Service to user to interact with the space, with a token
    """

    TOKEN_HEADER = 'api-token'

    def _get_request_header(self) -> Dict[str, str]:
        """
        Return the header for a request to space, with Api key and User if exists
        """
        headers = self._get_request_header()
        # Header with the Api Key
        headers[self.TOKEN_HEADER] = '1'

        return headers
