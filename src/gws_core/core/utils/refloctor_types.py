

from typing import Any, Dict, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO


# enum
class MethodDocType(str):
    CLASSMETHOD = "classmethod"
    STATICMETHOD = "staticmethod"
    BASICMETHOD = None


class MethodArgDoc(BaseModelDTO):
    arg_name: str
    arg_type: str
    arg_default_value: str


class MethodDocFunction():
    name: str
    func: Any

    def __init__(self, name: str, func: Any):
        # if name not str
        if not isinstance(name, str):
            raise ValueError("name should be str")
        self.name = name
        self.func = func


class MethodDoc(BaseModelDTO):
    name: str
    doc: Optional[str]
    args: List[MethodArgDoc]
    return_type: Optional[str]
    method_type: Optional[str]


class ClassicClassDocDTO(BaseModelDTO):
    name: str
    doc: Optional[str]
    methods: Optional[List[MethodDoc]]
    variables: Optional[Dict]
