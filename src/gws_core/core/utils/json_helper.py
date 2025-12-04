from typing import Any

from simplejson import dumps, loads


class JSONHelper:
    @staticmethod
    def safe_dumps(dict_data: dict) -> str:
        """
        Convert a dict to a string that can be used in a json file
        Stringify all python object to json using str method
        Replace NaN, inf by null
        """
        return dumps(dict_data, ignore_nan=True, iterable_as_array=True, default=str)

    @staticmethod
    def convert_dict_to_json(dict_data: dict) -> Any:
        """
        Convert a dict to a json dict that can be used in a json file
        Stringify all python object to json using str method
        Replace NaN, inf by null
        """
        return loads(JSONHelper.safe_dumps(dict_data))

    @staticmethod
    def extract_json_structure(data, parent_key="") -> Any:
        if isinstance(data, dict):
            structure = {}
            for key, value in data.items():
                new_key = f"{parent_key}.{key}" if parent_key else key
                structure[key] = JSONHelper.extract_json_structure(value, new_key)
            return structure
        elif isinstance(data, list):
            if len(data) > 0:
                return [JSONHelper.extract_json_structure(data[0], parent_key)]
            else:
                return []
        else:
            if data is None:
                return "any"
            # use the type to string in Utils
            return type(data).__name__
