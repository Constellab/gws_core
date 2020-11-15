# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pydantic import create_model

class Query:

    @classmethod
    def parse( cls, get_params: str = "", Model=None):
        data = {}
        tab = get_params.split(",")
        for d in tab:
            kv = d.split(":")
            data[kv[0]] = kv[1]
        
        if Model == None:
            Param = create_model('Param', **data)
            p = Param()
        else:
            p = Model(**data)

        return p

    @classmethod
    def select_query_to_list(cls, Q, return_format=""):
        _list = []
        if return_format.lower() == "json":
            for o in Q:
                _list.append(o.as_json())
        else:
            for o in Q:
                _list.append(o)
        
        return _list