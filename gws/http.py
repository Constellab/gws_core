# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import status, HTTPException

class HTTPBadRequest(HTTPException):
    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, **kwargs)
        
class HTTPUnauthorized(HTTPException):
    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, **kwargs)
        
class HTTPForbiden(HTTPException):
    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, **kwargs)
        
class HTTPNotFound(HTTPException):
    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, **kwargs)

class HTTPPaymentRequired(HTTPException):
    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, **kwargs)
        
class HTTPInternalServerError(HTTPException):
    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, **kwargs)

class HTTPBusy(HTTPException):
    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_226_IM_USED, **kwargs)
