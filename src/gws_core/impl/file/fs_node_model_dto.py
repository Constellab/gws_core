from gws_core.core.model.model_dto import BaseModelDTO


class FsNodeModelDTO(BaseModelDTO):
    id: str
    size: int
    is_file: bool
    name: str
    path: str
