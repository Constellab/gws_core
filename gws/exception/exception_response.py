from typing import Dict

from fastapi.responses import JSONResponse


class ExceptionResponse(JSONResponse):
    """
    Class to format the exception when an error is return
    """

    def __init__(self, status_code: int, code: str, detail: str, instance_id: str,
                 headers: Dict = None):
        """

        Arguments:
            status_code {int} -- HTTP Status
            code {str} -- Custom unique code
            detail {str} -- Detail of the error
            instance_id {str} -- Unique instance id of this instance of error

        """

        super().__init__(status_code=status_code, content={
            "code": code, "status": status_code, "detail": detail, "instance_id": instance_id},
            headers=headers)
