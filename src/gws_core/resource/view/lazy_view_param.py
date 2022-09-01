# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


class LazyViewParam():
    """Param for resource view. With this param you can define a method in your resource and reference it in func_name
    This function must return a ParamSpec and this is useful to configure spec dynamically.
    """

    func_name: str

    def __init__(self, func_name: str):
        """

        :param func_name: name of the resource function to call when retrieving the specs
        :type func_name: str
        """
        self.func_name = func_name
