

from typing import Optional, Type

from ..process.processable import Processable
from ..process.processable_model import ProcessableModel


class SubProcessableFactory():
    """Factory used by the ProtocolModel builder to instantiate processs of Protocol
    """

    def instantiate_processable(self, processable_uri: Optional[str],
                                processable_type: Type[Processable],
                                instance_name: str) -> ProcessableModel:
        pass
