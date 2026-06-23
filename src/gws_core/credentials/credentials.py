import builtins
from typing import Optional, final

from peewee import ModelSelect

from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.core.model.typed_db_field import (
    NullableJSONField,
    NullableTextField,
    TypedCharField,
    TypedEnumField,
)
from gws_core.credentials.credentials_type import CredentialsDTO

from .credentials_type import (
    CredentialsDataBase,
    CredentialsDataBasic,
    CredentialsDataLab,
    CredentialsDataOther,
    CredentialsDataS3,
    CredentialsDataS3LabServer,
    CredentialsType,
)


@final
class Credentials(ModelWithUser):
    name = TypedCharField(max_length=255, unique=True)
    type = TypedEnumField(choices=CredentialsType)

    description = NullableTextField()

    data = NullableJSONField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_saved() and not self.data:
            self.data = {}

    def to_dto(self) -> CredentialsDTO:
        return CredentialsDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            name=self.name,
            type=self.type,
            description=self.description,
        )

    def get_credentials_data_type(self) -> builtins.type[CredentialsDataBase]:
        return self.get_data_types().get(self.type)

    def get_data_object(self) -> CredentialsDataBase:
        data_type = self.get_credentials_data_type()
        return data_type.build_from_json(self.data, self.to_dto())

    @classmethod
    def find_by_name(cls, name: str) -> Optional["Credentials"]:
        return cls.select().where(Credentials.name == name).first()

    @classmethod
    def find_by_name_and_check(cls, name: str, type_: CredentialsType | None = None) -> "Credentials":
        credentials = cls.find_by_name(name)
        if not credentials:
            raise Exception(
                f"Credentials '{name}' not found, does it exist or was it renamed or deleted?"
            )

        if type_ is not None and credentials.type != type_:
            raise Exception(
                f"Credentials {name} does ont have the correct type. Expected type : '{type_}', found type : '{credentials.type}'. Was the credentials '{name}' updated?"
            )
        return credentials

    @classmethod
    def search_by_type(cls, type_: CredentialsType) -> ModelSelect:
        return cls.select().where(Credentials.type == type_)

    @classmethod
    def search_by_types(cls, types: list[CredentialsType]) -> ModelSelect:
        return cls.select().where(Credentials.type.in_(types))

    @classmethod
    def search_by_name(cls, name: str) -> ModelSelect:
        return cls.select().where(Credentials.name.contains(name))

    @classmethod
    def search_by_name_and_type(cls, name: str, type_: CredentialsType) -> ModelSelect:
        if not name:
            return cls.select().where(Credentials.type == type_)
        return cls.select().where(Credentials.name.contains(name), Credentials.type == type_)

    @classmethod
    def get_data_types(cls) -> dict[CredentialsType, builtins.type[CredentialsDataBase]]:
        return {
            CredentialsType.BASIC: CredentialsDataBasic,
            CredentialsType.S3: CredentialsDataS3,
            CredentialsType.S3_LAB_SERVER: CredentialsDataS3LabServer,
            CredentialsType.LAB: CredentialsDataLab,
            CredentialsType.OTHER: CredentialsDataOther,
        }

    class Meta:
        table_name = "gws_credentials"
        is_table = True
