# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional

from pydantic import BaseModel


class CentralProject(BaseModel):

    id: str
    code: str
    title: str
    children: Optional[List['CentralProject']]
