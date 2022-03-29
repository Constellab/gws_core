# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, List, Optional, TypedDict


class RichTextI(TypedDict):

    ops: List[Any]


class RichTextFigure(TypedDict):
    """Object representing a figure in a rich text

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    filename: str
    title: Optional[str]
    caption: Optional[str]
    width: int
    height: int
    naturalWidth: int
    naturalHeight: int


class RichText():
    """Class to manipulate the rich texts content

    :return: [description]
    :rtype: [type]
    """

    _content: RichTextI

    def __init__(self, rich_text_content: RichTextI) -> None:
        self._content = rich_text_content

    def is_empty(self) -> bool:
        return self._content is None or not self._content['ops'] or len(self._content['ops']) == 0 or \
            all(x['insert'] == '\n' for x in self._content['ops'])  # empty if all the ops only contain '\n'

    def get_figures(self) -> List[RichTextFigure]:
        figures: List[RichTextFigure] = []

        for op in self._content['ops']:
            if 'insert' in op and 'figure' in op['insert'] and isinstance(op['insert']['figure'], dict):
                figures.append(op['insert']['figure'])

        return figures
