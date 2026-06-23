from abc import abstractmethod
from typing import Any, ClassVar

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import StrParam
from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.credentials.credentials_decorator import credentials_type

############################ DTO ############################


class CredentialsTypeDTO(BaseModelDTO):
    """Metadata describing a registered credentials type (without its specs)."""

    type: str
    brick_name: str
    human_name: str
    short_description: str | None = None


class CredentialsDTO(ModelWithUserDTO):
    name: str
    type: CredentialsTypeDTO
    description: str | None = None


class SaveCredentialsDTO(BaseModelDTO):
    name: str
    type: str
    description: str | None = None
    data: Any


############################ DATA ############################


class CredentialsDataTypeSpecDTO(CredentialsTypeDTO):
    """DTO to get the spec  to configure the credentials data of a specific type"""

    specs: dict[str, ParamSpecDTO]


class CredentialsDataSpecsDTO(BaseModelDTO):
    """DTO to get the specs of credentaials all data types"""

    data_specs: list[CredentialsDataTypeSpecDTO]


class CredentialsDataBase(BaseModelDTO):
    # this field contains meta info about the credentials
    meta: CredentialsDTO | None = None

    # set by the @credentials_type decorator: the name passed to the decorator,
    # unique within the declaring brick.
    # ClassVar so pydantic treats them as class-level metadata, not model fields
    # (otherwise building a data object manually would require them as arguments).
    __credentials_type_name__: ClassVar[str]

    # set by the @credentials_type decorator: globally unique id of the form
    # '<brick_name>.<credentials_type_name>'. It is what gets stored in the
    # gws_credentials.type column.
    __credentials_type_id__: ClassVar[str]

    # set by the @credentials_type decorator: the name of the brick that declares
    # this credentials data class.
    __credentials_type_brick_name__: ClassVar[str]

    # set by the @credentials_type decorator: human readable name shown in the
    # interface (defaults to the unique name).
    __credentials_type_human_name__: ClassVar[str]

    # set by the @credentials_type decorator: short description shown in the
    # interface (optional).
    __credentials_type_short_description__: ClassVar[str | None] = None

    @classmethod
    def get_type_id(cls) -> str:
        """Return the globally unique id of this credentials data type
        (``<brick_name>.<unique_name>``), set by the @credentials_type decorator."""
        return cls.__credentials_type_id__

    @classmethod
    def get_brick_name(cls) -> str:
        """Return the name of the brick that declares this credentials data type,
        set by the @credentials_type decorator."""
        return cls.__credentials_type_brick_name__

    @classmethod
    def get_human_name(cls) -> str:
        """Return the human readable name of this credentials data type,
        set by the @credentials_type decorator."""
        return cls.__credentials_type_human_name__

    @classmethod
    def get_short_description(cls) -> str | None:
        """Return the short description of this credentials data type,
        set by the @credentials_type decorator."""
        return cls.__credentials_type_short_description__

    @classmethod
    def get_type_dto(cls) -> "CredentialsTypeDTO":
        """Return the metadata of this credentials type (id, brick, human name,
        description) without its specs."""
        return CredentialsTypeDTO(
            type=cls.get_type_id(),
            brick_name=cls.get_brick_name(),
            human_name=cls.get_human_name(),
            short_description=cls.get_short_description(),
        )

    @classmethod
    @abstractmethod
    def get_specs(cls) -> ConfigSpecs:
        """Get the specs of the credentials data"""

    @classmethod
    def get_spec_dto(cls) -> dict[str, ParamSpecDTO]:
        """Get the specs of the credentials data in DTO format"""
        return cls.get_specs().to_dto()

    @classmethod
    def build_from_json(cls, json_: dict, meta: CredentialsDTO | None = None) -> "CredentialsDataBase":
        data = cls.from_json(json_)
        data.meta = meta
        return data

    def convert_to_dict(self) -> dict:
        # convert the data to dict, remove the meta
        dict_ = self.to_json_dict()
        del dict_["meta"]
        return dict_


@credentials_type(
    "s3",
    human_name="S3",
    short_description="Credentials to connect to an S3 bucket",
)
class CredentialsDataS3(CredentialsDataBase):
    """Format of the data for S3 credentials"""

    endpoint_url: str
    region: str
    access_key_id: str
    secret_access_key: str
    bucket: str | None = None

    @classmethod
    def get_specs(cls) -> ConfigSpecs:
        return ConfigSpecs(
            {
                "endpoint_url": StrParam(human_name="Endpoint URL"),
                "region": StrParam(human_name="Region"),
                "access_key_id": StrParam(human_name="Access Key ID"),
                "secret_access_key": StrParam(human_name="Secret Access Key"),
                "bucket": StrParam(human_name="Bucket", optional=True),
            }
        )


@credentials_type(
    "s3_lab_server",
    human_name="S3 lab server",
    short_description="Credentials for the lab acting as an S3 server",
)
class CredentialsDataS3LabServer(CredentialsDataBase):
    """Format of the data for credentials for the lab acting as an S3 server"""

    access_key_id: str
    secret_access_key: str
    bucket: str
    bucket_local_path: str

    @classmethod
    def get_specs(cls) -> ConfigSpecs:
        return ConfigSpecs(
            {
                "access_key_id": StrParam(human_name="Access Key ID"),
                "secret_access_key": StrParam(human_name="Secret Access Key"),
                "bucket": StrParam(human_name="Name of the local S3 bucket"),
                "bucket_local_path": StrParam(
                    human_name="Local Directory",
                    short_description="The local directory where the files uploaded to S3 bucket is stored. Warning: use a safe directory path.",
                ),
            }
        )


@credentials_type(
    "basic",
    human_name="Basic",
    short_description="Username / password credentials",
)
class CredentialsDataBasic(CredentialsDataBase):
    """Format of the data for Basic credentials"""

    username: str
    password: str
    url: str | None = None

    @classmethod
    def get_specs(cls) -> ConfigSpecs:
        return ConfigSpecs(
            {
                "username": StrParam(human_name="Username"),
                "password": StrParam(human_name="Password"),
                "url": StrParam(human_name="URL", optional=True),
            }
        )


@credentials_type(
    "lab",
    human_name="Lab",
    short_description="Credentials to connect two data labs",
)
class CredentialsDataLab(CredentialsDataBase):
    """Format of the data for data lab credentials. Useful for connecting 2 data labs"""

    api_key: str

    @classmethod
    def get_specs(cls) -> ConfigSpecs:
        return ConfigSpecs(
            {
                "api_key": StrParam(human_name="Api key", min_length=20),
            }
        )


# Format of the data for other credentials
# A simple string to string dictionary
# When convert to and from json the data will be converted to a list of key value pairs for ParamSet
@credentials_type(
    "other",
    human_name="Other",
    short_description="Custom key / value credentials",
)
class CredentialsDataOther(CredentialsDataBase):
    data: dict[str, str]

    @classmethod
    def get_specs(cls) -> ConfigSpecs:
        return ConfigSpecs(
            {
                "data": ParamSet(
                    ConfigSpecs(
                        {
                            "key": StrParam(human_name="Key"),
                            "value": StrParam(human_name="Value"),
                        }
                    ),
                    human_name="Custom data",
                    short_description="List of key value pairs",
                )
            }
        )

    @classmethod
    def build_from_json(cls, json_: dict, meta: CredentialsDTO | None = None) -> "CredentialsDataBase":
        """Override to convert ParamSet list to basic dict"""
        data_dict = {d["key"]: d["value"] for d in json_["data"]}
        return super().build_from_json({"data": data_dict}, meta)

    def convert_to_dict(self) -> dict:
        """Override to convert the data dict to list of key value pairs for ParamSet"""
        dict_ = super().convert_to_dict()
        dict_["data"] = [{"key": k, "value": v} for k, v in self.data.items()]
        return dict_
