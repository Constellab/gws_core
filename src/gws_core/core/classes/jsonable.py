
from abc import abstractmethod
from typing import Dict, List


class Jsonable():
    """Any object that support to_json method

    :param List: [description]
    :type List: [type]
    """
    @abstractmethod
    def to_json(self, **kwargs) -> dict:
        pass


class ListJsonable(List[Jsonable]):
    """Basic list that support to_json method

    :param List: [description]
    :type List: [type]
    """

    def to_json(self, **kwargs) -> List[dict]:
        _json = []
        for obj in self:
            _json.append(obj.to_json(**kwargs))

        return _json


class DictJsonable(Dict[str, Jsonable]):
    """Basic dict that support to_json method

    :param List: [description]
    :type List: [type]
    """

    def to_json(self, **kwargs) -> Dict[str, dict]:
        _json = {}
        for key, obj in self.items():
            _json[key] = obj.to_json(**kwargs)

        return _json
