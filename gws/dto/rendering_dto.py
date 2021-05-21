# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional
from pydantic import BaseModel

# DTO to render ViewModel
class RenderingDTO(BaseModel):
    title: str = ""
    description: str = ""
    render: str = "as_json"
    params: dict = {}
    metadata: dict = {}
