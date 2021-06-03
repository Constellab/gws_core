# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import inspect
from typing import List, Union
from peewee import CharField
from gws.model import Viewable

class Path:
    """
    Path type class
    """
    pass


class URL:
    """
    URL type class
    """
    pass

# ####################################################################
#
# ProcessType class
#
# ####################################################################


class ProcessType(Viewable):
    """
    ProcessType class. This class allows storing information on all the types of the processes in the system.

    :property ptype: The type of the related process.
    :type ptype: `str`
    :property base_ptype: The base type of the related process. The base type is either `gws.model.Process` or `gws.model.Protocol`
    :type base_ptype: `str`
    """

    ptype: str = CharField(null=True, index=True, unique=True)
    base_ptype: str = CharField(null=True, index=True)

    _table_name = 'gws_process_type'

    def to_json(self, *, stringify: bool = False, prettify: bool = False, **kwargs) -> Union[str, dict]:
        from gws.service.model_service import ModelService

        _json = super().to_json(**kwargs)
        model_t = ModelService.get_model_type(self.ptype)
        specs = model_t.input_specs
        _json["input_specs"] = {}
        for name in specs:
            _json["input_specs"][name] = []
            t_list = specs[name]
            if not isinstance(t_list, tuple):
                t_list = (t_list, )

            for t in t_list:
                if t is None:
                    _json["input_specs"][name].append(None)
                else:
                    _json["input_specs"][name].append(t.full_classname())

        specs = model_t.output_specs
        _json["output_specs"] = {}
        for name in specs:
            _json["output_specs"][name] = []
            t_list = specs[name]
            if not isinstance(t_list, tuple):
                t_list = (t_list, )

            for t in t_list:
                if t is None:
                    _json["output_specs"][name].append(None)
                else:
                    _json["output_specs"][name].append(t.full_classname())

        _json["config_specs"] = model_t.config_specs
        for k in _json["config_specs"]:
            spec = _json["config_specs"][k]
            if "type" in spec and isinstance(spec["type"], type):
                t_str = spec["type"].__name__
                _json["config_specs"][k]["type"] = t_str
        
        _json["data"]["title"] = model_t.title
        _json["data"]["description"] = model_t.description
        _json["data"]["doc"] = inspect.getdoc(model_t)

        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

    def get_ptypes_array(self) -> List[str]:
        """
        Return the ptypes as an array by splitting with .
        """
        return self.ptype.split('.')

# ####################################################################
#
# ResourceType class
#
# ####################################################################


class ResourceType(Viewable):
    """
    ResourceType class. This class allows storing information on all the types of the resources in the system.

    :property rtype: The type of the related resource.
    :type rtype: `str`
    :property base_rtype: The base type of the related resource. The base type is either `gws.model.Resource`
    :type base_ptype: `str`
    """

    rtype = CharField(null=True, index=True, unique=True)
    base_rtype = CharField(null=True, index=True)
    
    _table_name = 'gws_resource_type'


    def to_json(self, *, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        from gws.service.model_service import ModelService
        
        _json = super().to_json(**kwargs)
        model_t = ModelService.get_model_type(self.rtype)

        if not _json.get("data"):
            _json["data"] = {}

        _json["data"]["title"] = model_t.title
        _json["data"]["description"] = model_t.description
        _json["data"]["doc"] = inspect.getdoc(model_t)

        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
