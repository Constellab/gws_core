# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import status, HTTPException
from gws.logger import Logger, Error

class HTTPError(HTTPException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #message = f"status code = {self.status_code}, detail = {self.detail}"
        #Logger.error(message)

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

async def async_error_track(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Error as err:
            raise HTTPInternalServerError(detail=err.message)
        except Exception as err:
            Logger.error(f"{err}")
            raise HTTPInternalServerError(detail=err.message)
        except HTTPError as err:
            message = f"HTTPError: status_code = {err.status_code}, detail = {err.detail}"
            Logger.error(message)
            raise err
            
    return wrapper