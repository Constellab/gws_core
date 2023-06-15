# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from peewee import ModelSelect

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchBuilder, SearchParams
from gws_core.core.utils.settings import Settings
from gws_core.credentials.credentials_search_builder import \
    CredentialsSearchBuilder
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

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

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
