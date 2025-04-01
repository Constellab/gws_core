

from abc import abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import StrParam
from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.core.utils.settings import Settings


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
    data: Any


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
        return cls.get_specs().to_dto()

    @classmethod
    def build_from_json(cls, json_: dict, meta: CredentialsDTO = None) -> 'CredentialsDataBase':
        data = cls.from_json(json_)
        data.meta = meta
        return data

    def convert_to_dict(self) -> Dict:
        # convert the data to dict, remove the meta
        dict_ = self.to_json_dict()
        del dict_['meta']
        return dict_


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
        return ConfigSpecs({
            "endpoint_url": StrParam(human_name="Endpoint URL"),
            "region": StrParam(human_name="Region"),
            "access_key_id": StrParam(human_name="Access Key ID"),
            "secret_access_key": StrParam(human_name="Secret Access Key"),
            "bucket": StrParam(human_name="Bucket", optional=True),
        })


class CredentialsDataBasic(CredentialsDataBase):
    """Format of the data for Basic credentials
    """
    username: str
    password: str
    url: Optional[str] = None

    @classmethod
    def get_specs(cls) -> ConfigSpecs:
        return ConfigSpecs({
            "username": StrParam(human_name="Username"),
            "password": StrParam(human_name="Password"),
            "url": StrParam(human_name="URL", optional=True),
        })


class CredentialsDataLab(CredentialsDataBase):
    """Format of the data for data lab credentials. Useful for connecting 2 data labs
    """
    lab_domain: str
    api_key: str
    sub_domain_api_override: Optional[str] = None

    @classmethod
    def get_specs(cls) -> ConfigSpecs:
        return ConfigSpecs({
            "lab_domain": StrParam(human_name="Lab domain",
                                   short_description="The domain is the part of the URL that comes after the https://lab and before the first /"),
            "api_key": StrParam(human_name="Api key", min_length=20),
            "sub_domain_api_override": StrParam(human_name="Sub domain API override", short_description="Leave empty for default. Set 'glab-dev' for dev api",
                                                optional=True),
        })

    def get_lab_api_url(self) -> str:
        """Get the lab api url
        """
        sub_domain = self.sub_domain_api_override if self.sub_domain_api_override else Settings.prod_api_sub_domain()
        return f"https://{sub_domain}.{self.lab_domain}"


# Format of the data for other credentials
# A simple string to string dictionary
# When convert to and from json the data will be converted to a list of key value pairs for ParamSet
class CredentialsDataOther(CredentialsDataBase):

    data: Dict[str, str]

    @classmethod
    def get_specs(cls) -> ConfigSpecs:
        return ConfigSpecs({
            "data": ParamSet(ConfigSpecs({
                "key": StrParam(human_name="Key"),
                "value": StrParam(human_name="Value"),
            }),
                human_name="Custom data",
                short_description="List of key value pairs")
        })

    @classmethod
    def build_from_json(cls, json_: dict, meta: CredentialsDTO = None) -> 'CredentialsDataBase':
        """Override to convert ParamSet list to basic dict
        """
        data_dict = {d['key']: d['value'] for d in json_['data']}
        return super().build_from_json({'data': data_dict}, meta)

    def convert_to_dict(self) -> Dict:
        """ Override to convert the data dict to list of key value pairs for ParamSet
        """
        dict_ = super().convert_to_dict()
        dict_['data'] = [{'key': k, 'value': v} for k, v in self.data.items()]
        return dict_
