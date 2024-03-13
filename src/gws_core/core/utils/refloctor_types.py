

from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO


class MethodArgDoc(BaseModelDTO):
    arg_name: str
    arg_type: str
    arg_default_value: str


class MethodDoc(BaseModelDTO):
    name: str
    doc: Optional[str]
    args: List[MethodArgDoc]
    return_type: Optional[str]
