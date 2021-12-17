
# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict

from typing_extensions import TypedDict


class TransformerDict(TypedDict):
    """Dict to call a transformer

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    typing_name: str
    config_values: Dict[str, Any]
