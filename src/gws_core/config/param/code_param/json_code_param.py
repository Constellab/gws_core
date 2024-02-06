# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.param.param_spec import TextParam
from gws_core.config.param.param_spec_decorator import param_spec_decorator


@param_spec_decorator()
class JsonCodeParam(TextParam):
    """Param for json code. It shows a simple json IDE
      in the interface to provide code for json.
      The value of this param is a string containing the json code
      with each line separated by a newline character (\n).

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_str_type(cls) -> str:
        return "json_code_param"
