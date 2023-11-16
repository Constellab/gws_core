# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from enum import Enum
from typing import Any, Dict, List, Optional, Set

from typing_extensions import TypedDict


class RichTextOps(TypedDict):
    insert: Any
    attributes: Optional[Dict[str, Any]]


class RichTextI(TypedDict):

    ops: List[RichTextOps]


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
    id: str
    resource_id: str
    experiment_id: str
    view_method_name: str
    view_config: Dict[str, Any]
    title: Optional[str]
    caption: Optional[str]
    # technical_info: List[Dict]


class RichText():
    """Class to manipulate the rich texts content

    :return: [description]
    :rtype: [type]
    """

    _content: RichTextI

    def __init__(self, rich_text_content: RichTextI) -> None:
        if not isinstance(rich_text_content, dict) or 'ops' not in rich_text_content:
            raise Exception('The content is not correclty formatted')
        self._content = rich_text_content

    def is_empty(self) -> bool:
        return self._content is None or not self._content['ops'] or len(self._content['ops']) == 0 or \
            all(x['insert'] == '\n' for x in self._content['ops'])  # empty if all the ops only contain '\n'

    def get_figures(self) -> List[RichTextFigure]:
        return self.get_special_ops(RichTextSpecialOps.FIGURE)

    def get_resource_views(self) -> List[RichTextResourceView]:
        return self.get_special_ops(RichTextSpecialOps.RESOURCE_VIEW)

    def has_resource_view(self, view_config_id: str) -> bool:
        """Check if the rich text contains a resource view with the given view_config_id
        """
        resource_views: List[RichTextResourceView] = self.get_resource_views()
        return any(rv['view_config']['id'] == view_config_id for rv in resource_views)

    def get_associated_resources(self) -> Set[str]:
        resource_views: List[RichTextResourceView] = self.get_resource_views()
        return {rv['resource_id'] for rv in resource_views}

    def get_special_ops(self, ops_name: RichTextSpecialOps) -> List[Any]:
        special_ops: List[RichTextFigure] = []

        for op in self._content['ops']:
            if 'insert' in op and isinstance(op['insert'], dict)  \
                    and ops_name.value in op['insert'] \
                    and isinstance(op['insert'][ops_name.value], dict):
                special_ops.append(op['insert'][ops_name.value])

        return special_ops

    def add_resource_views(self, resource_view: RichTextResourceView, variable_name: str = None) -> None:

        insert = {RichTextSpecialOps.RESOURCE_VIEW.value: resource_view}
        if variable_name is None:
            self._append_element(insert)
        else:
            self._insert_element(variable_name, insert)

    def _append_element(self, insert: Any, attributes: dict = None) -> None:
        element = {"insert": insert}

        if attributes:
            element["attributes"] = attributes
        self._content['ops'].append(element)

    def _insert_element(self, variable_name: str, insert: Any, attributes: dict = None) -> None:
        element = {"insert": insert}

        if attributes:
            element["attributes"] = attributes

        op_index = 0
        variable_name = self._format_variable_name(variable_name)
        while op_index < len(self._content['ops']):
            current_op = self._content['ops'][op_index]

            # if the op contains the variable name, split the string
            if 'insert' in current_op and isinstance(
                    current_op['insert'],
                    str) and variable_name in current_op['insert']:
                # split the string
                splitted = current_op['insert'].split(variable_name)

                # remove current op
                self._content['ops'].pop(op_index)

                # replace the current op by 3 ops (before, variable, after)
                if splitted[0]:
                    # add a \n at the end to finish the previous op
                    self._content['ops'].insert(op_index, {'insert': splitted[0] + '\n'})
                    op_index += 1

                self._content['ops'].insert(op_index, element)
                op_index += 1

                if splitted[1]:
                    self._content['ops'].insert(op_index, {'insert': splitted[1]})
                    op_index += 1
            else:
                op_index += 1

    def get_content(self) -> RichTextI:
        return self._content

    def replace_variable(self, variable_name: str, value: str) -> None:
        """Replace the variable in the rich text content
        """
        variable_name = self._format_variable_name(variable_name)
        for op in self._content['ops']:
            if 'insert' in op and isinstance(op['insert'], str) and variable_name in op['insert']:
                op['insert'] = op['insert'].replace(variable_name, value)

    def add_paragraph(self, paragraph: str) -> None:
        """Add a paragraph to the rich text content
        """
        self._append_element(paragraph)

    def replace_resource_views_with_variables(self):
        """Method to remove the resource view from the rich text content
         and replace it when variables
        """

        op_index = 0
        view_index = 1
        for ope in self._content['ops']:
            if 'insert' in ope and isinstance(ope['insert'], dict) \
                    and RichTextSpecialOps.RESOURCE_VIEW.value in ope['insert'] \
                    and isinstance(ope['insert'][RichTextSpecialOps.RESOURCE_VIEW.value], dict):
                variable = self._format_variable_name(f"figure_{view_index}") + '\n'
                ops: RichTextOps = {'insert': variable}
                self._content['ops'][op_index] = ops
                view_index += 1
            op_index += 1

    def _format_variable_name(self, variable_name: str) -> str:
        return f'${variable_name}$'
