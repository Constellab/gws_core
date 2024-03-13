

from typing import Any, Dict

from typing_extensions import TypedDict


class TransformerDict(TypedDict):
    """Dict to call a transformer

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    typing_name: str
    config_values: Dict[str, Any]
