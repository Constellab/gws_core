

from abc import abstractmethod
from enum import Enum
from typing import Dict, List, Optional

from gws_core.config.config_specs_helper import ConfigSpecsHelper
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import StrParam
from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO


class CredentialsType(Enum):
    """
    Different types of credentials
    """
    BASIC = "BASIC"
    S3 = "S3"
    LAB = "LAB"
    OTHER = "OTHER"

############################ DTO ############################


class CredentialsDTO(ModelWithUserDTO):
    name: str
    type: CredentialsType
    description: Optional[str] = None


class SaveCredentialsDTO(BaseModelDTO):
    name: str
    type: CredentialsType
    description: Optional[str] = None
    data: dict


############################ DATA ############################

class CredentialsDataTypeSpecDTO(BaseModelDTO):
    """DTO to get the spec  to configure the credentials data of a specific type
    """
    type: CredentialsType
    specs: Dict[str, ParamSpecDTO]


class CredentialsDataSpecsDTO(BaseModelDTO):
    """DTO to get the specs of credentaials all data types
    """
    data_specs: List[CredentialsDataTypeSpecDTO]


class CredentialsDataBase(BaseModelDTO):
    # this field contains meta info about the credentials
    meta: Optional[CredentialsDTO] = None

    @classmethod
    @abstractmethod
    def get_specs(cls) -> ConfigSpecs:
        """Get the specs of the credentials data
        """

    @classmethod
    def get_spec_dto(cls) -> Dict[str, ParamSpecDTO]:
        """Get the specs of the credentials data in DTO format
        """
        return ConfigSpecsHelper.config_specs_to_dto(cls.get_specs())


class CredentialsDataS3(CredentialsDataBase):
    """Format of the data for S3 credentials
    """
    endpoint_url: str
    region: str
    access_key_id: str
    secret_access_key: str
    bucket: Optional[str] = None

    @classmethod
    def get_specs(cls) -> ConfigSpecs:
        return {
            "endpoint_url": StrParam(human_name="Endpoint URL"),
            "region": StrParam(human_name="Region"),
            "access_key_id": StrParam(human_name="Access Key ID"),
            "secret_access_key": StrParam(human_name="Secret Access Key"),
            "bucket": StrParam(human_name="Bucket", optional=True),
        }


class CredentialsDataBasic(CredentialsDataBase):
    """Format of the data for Basic credentials
    """
    username: str
    password: str
    url: Optional[str] = None

    @classmethod
    def get_specs(cls) -> ConfigSpecs:
        return {
            "username": StrParam(human_name="Username"),
            "password": StrParam(human_name="Password"),
            "url": StrParam(human_name="URL", optional=True),
        }


class CredentialsDataLab(CredentialsDataBase):
    """Format of the data for data lab credentials. Useful for connecting 2 data labs
    """
    lab_domain: str
    api_key: str

    @classmethod
    def get_specs(cls) -> ConfigSpecs:
        return {
            "lab_domain": StrParam(human_name="Lab domain",
                                   short_description="The domain is the part of the URL that comes after the https://lab and before the first /"),
            "api_key": StrParam(human_name="Api key"),
        }


# Format of the data for other credentials
# A simple string to string dictionary
class CredentialsDataOther(CredentialsDataBase):

    data: Dict[str, str]

    @classmethod
    def get_specs(cls) -> ConfigSpecs:
        return {
            "data": ParamSet({
                "key": StrParam(human_name="Key"),
                "value": StrParam(human_name="Value"),
            }),
        }
