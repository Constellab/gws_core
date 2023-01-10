# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.core.classes.validator import StrValidator, Validator

from ..param_spec import ParamSpec


class PerlCodeParam(ParamSpec[str]):
    """Param for perl code. It shows a simple perl IDE
      in the interface to provide code for perl.
      The value of this param is a string containing the perl code
      with each line separated by a newline character (\n).

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_str_type(cls) -> str:
        return "perl_code_param"

    def _get_validator(self) -> Validator:
        return StrValidator()
