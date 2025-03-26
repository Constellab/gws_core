
from typing import Any, Dict, Optional, TypedDict

from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_spec_decorator import (ParamaSpecType,
                                                        param_spec_decorator)
from gws_core.config.param.param_types import (ParamSpecDTO, ParamSpecTypeStr,
                                               ParamSpecVisibilty)
from gws_core.core.classes.validator import StrValidator

from .credentials import Credentials
from .credentials_type import CredentialsDataBase, CredentialsType


class CredentialsParamAdditionalInfo(TypedDict):
    """Additional info for credentials param"""

    credentials_type: Optional[str]


@param_spec_decorator(type_=ParamaSpecType.LAB_SPECIFIC)
class CredentialsParam(ParamSpec):
    """ Credentials params spec. When used, the end user will be able to select a credentials
    from the list of credentials available in the lab. The config stores only the credentials name
    but not the credentials data (key, password).
    The credentials data is retrieved from the credentials service just before the execution of the task or view.

    The accessible value in task is a CredentialsDataBase, it depends on the credentials type.
    See the documentation of the credentials type for more info.

    """

    additional_info: Optional[CredentialsParamAdditionalInfo]

    def __init__(self,
                 credentials_type: CredentialsType = None,
                 optional: bool = False,
                 visibility: ParamSpecVisibilty = "public",
                 human_name: Optional[str] = None,
                 short_description: Optional[str] = None,
                 ):
        """
        :param credentials_type: Type of credentials to use for this param (if empty, any credentials can be used)
        :type credentials_type: CredentialsType
        :param optional: See default value
        :type optional: Optional[str]
        :param visibility: Visibility of the param, see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :type default: Optional[ConfigParamType]
        :param human_name: Human readable name of the param, showed in the interface
        :type human_name: Optional[str]
        :param short_description: Description of the param, showed in the interface
        :type short_description: Optional[str]
        """
        self.additional_info = {
            "credentials_type": credentials_type.value if credentials_type is not None else None,
        }

        if human_name is None:
            if credentials_type is not None:
                human_name = f"Select {credentials_type.value} credentials"
            else:
                human_name = "Select credentials"

        super().__init__(
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )
        self.credentials_type = credentials_type

    @classmethod
    def get_str_type(cls) -> ParamSpecTypeStr:
        return ParamSpecTypeStr.CREDENTIALS

    def build(self, value: Any) -> CredentialsDataBase:
        if not value:
            return None

        # retrieve the credentials and return it
        credentials: Credentials = Credentials.find_by_name_and_check(value, self.credentials_type)
        return credentials.get_data_object()

    def validate(self, value: Any) -> str:

        if isinstance(value, Credentials):
            return value.name

        if isinstance(value, CredentialsDataBase) and value.meta:
            return value.meta.name

        # if this is the credentials object, retrieve the name
        # used when the credentials of a task are saved
        if isinstance(value, dict) and 'name' in value:
            value = value['name']

        validator = StrValidator()
        return validator.validate(value)

    @classmethod
    def get_default_value_param_spec(cls) -> "CredentialsParam":
        return CredentialsParam()

    @classmethod
    def get_additional_infos(cls) -> Dict[str, ParamSpecDTO]:
        return None
