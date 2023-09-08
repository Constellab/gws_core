# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from simplejson import dumps, loads


class JSONHelper():

    @staticmethod
    def convert_dict_to_json(dict_data: dict) -> str:
        """
        Convert a dict to a json dict that can be used in a json file
        Stringify all python object to json using str method
        Replace NaN, inf by null
        """
        return loads(dumps(dict_data, ignore_nan=True, iterable_as_array=True, default=str))
