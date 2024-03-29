
import json
from typing import Dict, Literal

from fastapi.responses import JSONResponse

# If error, the interface will show the messgae in an error box
# If info, the interface will show the message in a info box
ExceptionShowMode = Literal["error", "info"]


class ExceptionResponse(JSONResponse):
    """
    Class to format the exception when an error is return
    """

    def __init__(self, status_code: int, code: str, detail: str, instance_id: str,
                 show_as: ExceptionShowMode = 'error', headers: Dict = None):
        """

        Arguments:
            status_code {int} -- HTTP Status
            code {str} -- Custom unique code
            detail {str} -- Detail of the error
            instance_id {str} -- Unique instance id of this instance of error

        """

        super().__init__(status_code=status_code, content={
            "code": code, "status": status_code, "detail": detail, "instanceId": instance_id, "show_as": show_as},
            headers=headers)

    def get_json_body(self) -> dict:
        return json.loads(self.body.decode('utf8').replace("'", '"'))
