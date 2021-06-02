# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws.model import ProgressBar
from gws.http import *

from .base_service import BaseService

class ProgressBarService(BaseService):
     
    @classmethod
    def fetch_progress_bar(cls, uri: str) -> ProgressBar:
        
        try:
            return ProgressBar.get(ProgressBar.uri == uri)
        except Exception as err:
            raise HTTPNotFound(detail=f"No process bar found with uri {uri}", debug_error=err)