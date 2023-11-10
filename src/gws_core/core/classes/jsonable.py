
from abc import abstractmethod
from typing import Any, Dict, List, Union


class Jsonable():
    """Any object that support to_json method

    :param List: [description]
    :type List: [type]
    """
    @abstractmethod
    def to_json(self, **kwargs) -> Any:
        pass


class ListJsonable(Jsonable):
    """Basic list that support to_json method

    :param List: [description]
    :type List: [type]
    """

    list: List[Jsonable]

    def __init__(self, list_: List[Jsonable] = None):
        if list_ is None:
            list_ = []
        self.list = list_

    def to_json(self, **kwargs) -> List[Any]:
        _json = []
        for obj in self.list:
            _json.append(obj.to_json(**kwargs))

        return _json

    def append(self, jsonable: Union[Jsonable, List[Jsonable]]) -> None:
        if isinstance(jsonable, list):
            self.list.extend(jsonable)
        else:
            self.list.append(jsonable)


class DictJsonable(Jsonable):
    """Basic dict that support to_json method

    :param List: [description]
    :type List: [type]
    """

    dict: Dict[str, Jsonable]

    def __init__(self, dict_: Dict[str, Jsonable] = None):
        if dict_ is None:
            dict_ = {}
        self.dict = dict_

    def to_json(self, **kwargs) -> Dict[str, Any]:
        _json = {}
        for key, obj in self.dict.items():
            _json[key] = obj.to_json(**kwargs)

        return _json
