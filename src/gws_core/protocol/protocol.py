
from typing import Dict, List, TypedDict

from ..model.typing_register_decorator import TypingDecorator
from ..processable.processable import Processable
from ..processable.processable_model import ProcessableModel

# Typing names generated for the class Process
CONST_PROTOCOL_TYPING_NAME = "PROTOCOL.gws_core.Protocol"


class ProtocolCreateConfig(TypedDict):
    processes: Dict[str, ProcessableModel]

    connectors: List

    interfaces: Dict
    outerfaces: Dict


@TypingDecorator(unique_name="Protocol", object_type="PROTOCOL", hide=True)
class Protocol(Processable):

    def get_create_config(self) -> ProtocolCreateConfig:
        return {
            "processes": {},
            "connectors": [],
            "interfaces": {},
            "outerfaces": {},
        }
