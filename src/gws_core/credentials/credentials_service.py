

from typing import Any, List, Optional

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchBuilder, SearchParams
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.exception.exceptions.unauthorized_exception import \
    UnauthorizedException
from gws_core.core.utils.settings import Settings
from gws_core.credentials.credentials_search_builder import \
    CredentialsSearchBuilder
from gws_core.credentials.credentials_type import (CredentialsDataS3,
                                                   CredentialsType)
from gws_core.space.space_service import (ExternalCheckCredentialResponse,
                                          SpaceService)
from gws_core.user.user_credentials_dto import UserCredentialsDTO

from .credentials import Credentials
from .credentials_type import (CredentialsDataLab, CredentialsDataSpecsDTO,
                               CredentialsDataTypeSpecDTO, SaveCredentialsDTO)


class CredentialsService():

    @classmethod
    def create(cls, save_credentials: SaveCredentialsDTO) -> Credentials:
        credentials = cls._check_and_build_from_dto(save_credentials)
        return credentials.save()

    @classmethod
    def update(cls, id_: str, save_credentials: SaveCredentialsDTO) -> Credentials:
        credentials = cls._check_and_build_from_dto(save_credentials, id_)
        return credentials.save()

    @classmethod
    def _check_and_build_from_dto(cls, save_credentials: SaveCredentialsDTO, id_: str = None) -> Credentials:

        credentials: Credentials = None

        # check that another credentials with the same name does not exist
        if id_:
            credentials = Credentials.get_by_id_and_check(id_)
            other = Credentials.select().where(Credentials.id != id_, Credentials.name == save_credentials.name).first()
            if other:
                raise Exception("Credentials with this name already exists")
        else:
            other = Credentials.find_by_name(save_credentials.name)
            if other:
                raise Exception("Credentials with this name already exists")
            credentials = Credentials()

        credentials.name = save_credentials.name
        credentials.description = save_credentials.description
        credentials.type = save_credentials.type

        # check that the data is valid
        try:
            credentials_type = credentials.get_credentials_data_type()

            # build the data object to check the data
            data_obj = credentials_type.build_from_json(save_credentials.data)
            credentials.data = data_obj.convert_to_dict()
        except Exception as e:
            raise BadRequestException(f"Invalid credentials data: {str(e)}")
        return credentials

    @classmethod
    def delete(cls, credentials_id: str) -> None:
        return Credentials.delete_by_id(credentials_id)

    @classmethod
    def get_by_id_and_check(cls, credentials_id: str) -> Credentials:
        return Credentials.get_by_id_and_check(credentials_id)

    @classmethod
    def get_all(cls, page: int = 0,
                number_of_items_per_page: int = 20) -> Paginator[Credentials]:
        model_select = Credentials.select().order_by(Credentials.name)
        return Paginator(model_select, page, number_of_items_per_page)

    @classmethod
    def search(cls,
               search: SearchParams,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[Credentials]:

        search_builder: SearchBuilder = CredentialsSearchBuilder()

        return search_builder.add_search_params(search).search_page(page, number_of_items_per_page)

    @classmethod
    def get_credentials_data(cls, credentials_id: str, user_credentials: UserCredentialsDTO) -> dict:
        """Read the credentials details, need user credentials to double check
        """

        # skip the check with space in local dev env
        if not Settings.get_instance().is_local_dev_env():
            response: ExternalCheckCredentialResponse = SpaceService.check_credentials(user_credentials, False)

            if not response.status == 'OK':
                raise UnauthorizedException('Invalid credentials')

        credentials: Credentials = Credentials.get_by_id_and_check(credentials_id)

        return credentials.get_data_object().convert_to_dict()

    @classmethod
    def find_by_name(cls, name: str) -> Credentials:
        return Credentials.find_by_name(name)

    @classmethod
    def get_s3_credentials_data_by_access_key(cls, access_key_id: str) -> Optional[CredentialsDataS3]:
        """Return the S3 credentials that match the access key id
        """

        s3_credentials: List[Credentials] = Credentials.search_by_type(CredentialsType.S3)

        for credentials in s3_credentials:
            data: CredentialsDataS3 = credentials.get_data_object()
            if data.access_key_id == access_key_id:
                return data

        return None

    @classmethod
    def get_lab_credentials_data_by_api_key(cls, api_key: str) -> Optional[CredentialsDataLab]:
        """Return the lab credentials that match the api key
        """

        lab_credentials: List[Credentials] = Credentials.search_by_type(CredentialsType.LAB)

        for credentials in lab_credentials:
            data: CredentialsDataLab = credentials.get_data_object()
            if data.api_key == api_key:
                return data

        return None

    @classmethod
    def get_credentials_data_specs(cls) -> CredentialsDataSpecsDTO:
        """Return the specs of all credentials data types
        """
        data_types = Credentials.get_data_types()
        data_specs = []

        for type_, data_type in data_types.items():
            data_specs.append(CredentialsDataTypeSpecDTO(
                type=type_,
                specs=data_type.get_spec_dto()
            ))

        return CredentialsDataSpecsDTO(data_specs=data_specs)
