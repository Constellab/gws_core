# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
from fastapi import status, HTTPException
from gws.logger import Logger, Error

class HTTPError(HTTPException):
    def __init__(self, detail=None, debug_error=None, **kwargs):
        super().__init__(detail=detail, **kwargs)
        if debug_error:
            Logger.error(f"{debug_error}") #-> call error class for log treaceability; do not raise this exception
        Logger.error(f"{self}") #-> call error class for log treaceability; do not raise this exception

class HTTPBadRequest(HTTPError):
    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, **kwargs)
        
class HTTPUnauthorized(HTTPError):
    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, **kwargs)
        
class HTTPForbiden(HTTPError):
    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, **kwargs)
        
class HTTPNotFound(HTTPError):
    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, **kwargs)

class HTTPPaymentRequired(HTTPError):
    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, **kwargs)
        
class HTTPInternalServerError(HTTPError):
    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, **kwargs)

class HTTPBusy(HTTPError):
    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_226_IM_USED, **kwargs)
