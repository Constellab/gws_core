# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List, TypedDict


class TableHeaderInfo(TypedDict):
    """Object to represent the information about a table header (row, column)
    """
    name: str
    tags: Dict[str, str]


class TableMeta(TypedDict):
    """ Object that represent the table Meta information
    """
    row_tags: List[Dict[str, str]]
    column_tags: List[Dict[str, str]]
    row_tag_types: Dict[str, str]
    column_tag_types: Dict[str, str]
