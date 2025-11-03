

from typing import List, Type

from gws_core.brick.brick_model import BrickModel
from gws_core.brick.brick_service import BrickService
from gws_core.core.utils.logger import Logger
from gws_core.model.typing import Typing

from ..core.classes.paginator import Paginator
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.model import Model
from .typing_manager import TypingManager


class ModelService():

    _number_of_items_per_page = 20

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
    def fetch_model(cls, typing_name: str, id: str) -> Model:
        """
        Fetch a model

        :param type: The type of the model
        :type type: `str`
        :param id: The id of the model
        :type id: `str`
        :return: A model
        :rtype: instance of `gws.db.model.Model`
        """

        return TypingManager.get_object_with_typing_name_and_id(typing_name, id)

    @classmethod
    def fetch_list_of_models(cls,
                             typing_name: str,
                             page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Model]:

        model_type: Type[Model] = TypingManager.get_type_from_name(typing_name)

        if not issubclass(model_type, Model):
            raise BadRequestException("The requested type is not a Model")

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        query = model_type.select().order_by(model_type.created_at.desc())
        return Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def search(cls, typing_name: str, search_text: str,
               page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Model]:
        base_type: Type[Model] = TypingManager.get_type_from_name(typing_name)

        query = base_type.search(search_text)
        return Paginator(query, page=page, nb_of_items_per_page=number_of_items_per_page,
                         nb_max_of_items_per_page=cls._number_of_items_per_page)

    ############################################## MODIFY ############################################

    @classmethod
    def register_all_processes_and_resources(cls) -> None:
        TypingManager.save_object_types_in_db()
        cls.check_all_typings()

    @classmethod
    def check_all_typings(cls) -> None:
        """Method to check if all typing registered in BD exists"""

        bricks: List[BrickModel]

        try:
            bricks = list(BrickService.get_all_brick_models())
        except Exception as e:
            Logger.error(f"Error while getting bricks from the database: {str(e)}")
            return

        for brick in bricks:
            # don't check typing if the brick status is Crittical
            if brick.status == 'CRITICAL':
                continue

            try:
                list(Typing.select().where(Typing.brick == brick.name))
            except Exception as e:
                BrickService.log_brick_message(
                    brick_name=brick.name,
                    message=f"Error while getting typings from the database: {str(e)}",
                    status='CRITICAL')
                continue
