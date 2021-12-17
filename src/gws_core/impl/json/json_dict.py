# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...resource.r_field import DictRField
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator


@resource_decorator("JSONDict")
class JSONDict(Resource):

    data: dict = DictRField()

    def __init__(self, data: dict = None):
        super().__init__()
        if data is None:
            data = {}
        else:
            if not isinstance(data, dict):
                raise BadRequestException("The data must be an instance of dict")
        self.data = data

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __setitem__(self, key, val):
        self.data[key] = val

    def __str__(self):
        return super().__str__() + "\n" + \
            "Dictionnary:\n" + \
            self.data.__str__()
