# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Type

from ..core.classes.paginator import Paginator
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.model import Model
from ..core.service.base_service import BaseService
from .typing_manager import TypingManager


class ModelService(BaseService):

    ############################################## GET ############################################

    @classmethod
    def count_model(cls, typing_name: str) -> int:
        """
        Counts models
        """

        model_type: Type[Model] = TypingManager.get_type_from_name(typing_name)

        return cls.count_model_from_type(model_type)

    @classmethod
    def count_model_from_type(cls, model_type: Type[Model]) -> int:
        """
        Counts models
        """

        return model_type.select().count()

    # -- F --

    @classmethod
    def fetch_model(cls, typing_name: str, uri: str) -> Model:
        """
        Fetch a model

        :param type: The type of the model
        :type type: `str`
        :param uri: The uri of the model
        :type uri: `str`
        :return: A model
        :rtype: instance of `gws.db.model.Model`
        """

        return TypingManager.get_object_with_typing_name_and_uri(typing_name, uri)

    @classmethod
    def fetch_list_of_models(cls,
                             typing_name: str,
                             page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Model]:

        model_type: Type[Model] = TypingManager.get_type_from_name(typing_name)

        if not issubclass(model_type, Model):
            raise BadRequestException("The requested type is not a Model")

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        query = model_type.select().order_by(model_type.creation_datetime.desc())
        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    @classmethod
    def search(cls, typing_name: str, search_text: str,
               page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Model]:
        base_type: Type[Model] = TypingManager.get_type_from_name(typing_name)

        query = base_type.search(search_text)
        return Paginator(query, page=page, number_of_items_per_page=number_of_items_per_page,
                         nb_max_of_items_per_page=cls._number_of_items_per_page)

    ############################################## MODIFY ############################################

    @classmethod
    def register_all_processes_and_resources(cls) -> None:
        TypingManager.save_object_types_in_db()

    @classmethod
    def archive_model(cls, typing_name: str, uri: str) -> Model:
        return cls._set_archive(typing_name, uri, True)

    @classmethod
    def unarchive_model(cls, typing_name: str, uri: str) -> Model:
        return cls._set_archive(typing_name, uri, False)

    @classmethod
    def _set_archive(cls, typing_name: str, uri: str, archive: bool) -> Model:
        model: Model = TypingManager.get_object_with_typing_name_and_uri(typing_name, uri)

        return model.archive(archive)

    @classmethod
    def verify_model_hash(cls, typing_name: str, uri: str) -> bool:
        """
        Verify model hash

        :param type: The type of the model
        :type type: `str`
        :param uri: The uri of the model
        :type uri: `str`
        :return: True if the hash is valid, False otherwise
        :rtype: `bool`
        """

        model: Model = TypingManager.get_object_with_typing_name_and_uri(typing_name, uri)
        return model.verify_hash()
