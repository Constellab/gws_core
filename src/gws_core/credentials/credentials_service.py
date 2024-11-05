

from typing import List, Optional

from peewee import ModelSelect

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchBuilder, SearchParams
from gws_core.core.utils.settings import Settings
from gws_core.credentials.credentials_search_builder import \
    CredentialsSearchBuilder
from gws_core.credentials.credentials_type import (CredentialsDataS3,
                                                   CredentialsType)
from gws_core.space.space_service import (ExternalCheckCredentialResponse,
                                          SpaceService)
from gws_core.user.user_credentials_dto import UserCredentialsDTO

from .credentials import Credentials
from .credentials_dto import SaveCredentialDTO


class CredentialsService():

    @classmethod
    def create(cls, save_credentials: SaveCredentialDTO) -> Credentials:
        credentials = cls._check_and_build_from_dto(save_credentials)
        return credentials.save()

    @classmethod
    def update(cls, id: str, save_credentials: SaveCredentialDTO) -> Credentials:
        credentials = cls._check_and_build_from_dto(save_credentials, id)
        return credentials.save()

    @classmethod
    def _check_and_build_from_dto(cls, save_credentials: SaveCredentialDTO, id: str = None) -> Credentials:

        credentials: Credentials = None

        # check that another credentials with the same name does not exist
        if id:
            credentials = Credentials.get_by_id_and_check(id)
            other = Credentials.select().where(Credentials.id != id, Credentials.name == save_credentials.name).first()
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
        credentials.data = save_credentials.data
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
                raise Exception('Invalid credentials')

        credentials: Credentials = Credentials.get_by_id_and_check(credentials_id)
        return credentials.data

    @classmethod
    def find_by_name(cls, name: str) -> Credentials:
        return Credentials.find_by_name(name)

    @classmethod
    def get_s3_credentials_data_by_access_key(cls, access_key_id: str) -> Optional[CredentialsDataS3]:
        """Return the S3 credentials that match the access key id
        """

        s3_credentials: List[Credentials] = Credentials.search_by_type(CredentialsType.S3)

        for credentials in s3_credentials:
            data: CredentialsDataS3 = credentials.data
            if data.get('access_key_id') == access_key_id:
                return data

        return None
