# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

from gws_core.task.transformer.transformer_type import TransformerDict


class RichTextI(TypedDict):

    ops: List[Any]


class RichTextSpecialOps(Enum):
    """List the special ops type that can be used in rich text """
    FIGURE = 'figure'
    RESOURCE_VIEW = 'resource_view'


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


class RichTextResourceView(TypedDict):
    """Object representing a resource view in a rich text"""
    resource_id: str
    experiment_id: str
    view_method_name: str
    view_config: Dict[str, Any]
    transformers: List[TransformerDict]
    title: Optional[str]
    caption: Optional[str]


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
        return self.get_special_ops(RichTextSpecialOps.FIGURE)

    def get_resource_views(self) -> List[RichTextResourceView]:
        return self.get_special_ops(RichTextSpecialOps.RESOURCE_VIEW)

    def get_special_ops(self, ops_name: RichTextSpecialOps) -> List[Any]:
        special_ops: List[RichTextFigure] = []

        for op in self._content['ops']:
            if 'insert' in op and ops_name.value in op['insert'] and isinstance(op['insert'][ops_name.value], dict):
                special_ops.append(op['insert'][ops_name.value])

        return special_ops
