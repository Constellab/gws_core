# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, List, Optional, TypedDict


class RichTextI(TypedDict):

    ops: List[Any]


class RichTextFigure(TypedDict):
    filename: str
    url: str
    title: Optional[str]
    caption: Optional[str]
    width: int
    height: int
    naturalWidth: int
    naturalHeight: int


class RichText():

    _content: RichTextI

    def __init__(self, rich_text_content: RichTextI) -> None:
        self._content = rich_text_content

    def get_figures(self) -> List[RichTextFigure]:
        figures: List[RichTextFigure] = []

        for op in self._content['ops']:
            if 'insert' in op and 'figure' in op['insert'] and isinstance(op['insert']['figure'], dict):
                figures.append(op['insert']['figure'])

        return figures
