# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ..param_spec import TextParam


class JuliaCodeParam(TextParam):
    """Param for julia code. It shows a simple julia IDE
      in the interface to provide code for julia.
      The value of this param is a string containing the julia code
      with each line separated by a newline character (\n).

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_str_type(cls) -> str:
        return "julia_code_param"
