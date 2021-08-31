
from abc import abstractmethod
from typing import List


class Jsonable():
    """Any object that support to_json method

    :param List: [description]
    :type List: [type]
    """
    @abstractmethod
    def to_json(self, deep: bool = False, **kwargs) -> dict:
        pass


class ListJsonable(List[Jsonable]):
    """Basic list that support to_json method

    :param List: [description]
    :type List: [type]
    """

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        _json = []
        for obj in self:
            _json.append(obj.to_json(deep=deep, kwargs=kwargs))

        return _json
