

from gws_core.core.decorator.transaction import transaction

from ..config.config_types import ConfigParamsDict
from ..core.service.base_service import BaseService
from ..model.typing_manager import TypingManager
from ..process.process_model import ProcessModel


class ProcessService(BaseService):

    @classmethod
    def delete_process_from_uri(cls, typing_name: str, uri: str) -> None:
        process_model: ProcessModel = cls._get_process_model(typing_name, uri)

        cls.delete_process_model(process_model)

    @classmethod
    @transaction()
    def delete_process_model(cls, process_model: ProcessModel) -> None:
        process_model.delete_instance()

    @classmethod
    def _get_process_model(cls, typing_name: str, uri: str) -> ProcessModel:
        return TypingManager.get_object_with_typing_name_and_uri(typing_name, uri)
