import json
from typing import Literal

from fastapi.responses import JSONResponse

# If error, the interface will show the messgae in an error box
# If info, the interface will show the message in a info box
ExceptionShowMode = Literal["error", "info"]


class ExceptionResponse(JSONResponse):
    """
    Class to format the exception when an error is return
    """

    def __init__(
        self,
        status_code: int,
        detail: str,
        instance_id: str | None = None,
        request_id: str | None = None,
        code: str | None = None,
        show_as: ExceptionShowMode = "error",
        headers: dict | None = None,
    ):
        """

        Arguments:
            status_code {int} -- HTTP Status
            code {str} | None -- Custom unique code
            detail {str} -- Detail of the error
            instance_id {str} -- Unique instance id of this instance of error

        """

        super().__init__(
            status_code=status_code,
            content={
                "code": code,
                "status": status_code,
                "detail": detail,
                "instanceId": instance_id,
                "requestId": request_id,
                "show_as": show_as,
            },
            headers=headers,
        )

    def get_json_body(self) -> dict:
        return json.loads(self.body.decode("utf8").replace("'", '"'))
