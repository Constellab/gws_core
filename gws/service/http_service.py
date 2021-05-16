# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from starlette_context import context
from .base_service import BaseService

class HTTPService(BaseService):
    
    @classmethod
    def is_http_context(cls):
        try:
            context.data["is_http_context"] = True  #-> if not exception -> return True
            return True
        except:
            return False
    