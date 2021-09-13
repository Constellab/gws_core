# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type
from ..protocol.protocol import Protocol
from ..protocol.protocol_model import ProcessModel
from ..protocol.protocol_service import ProtocolService
from .experiment import Experiment
from .experiment_service import ExperimentService

class IExperiment:
    
    _protocolo_type: Type[Protocol]
    _protocol_model: ProcessModel
    _experiment: Experiment

    def __init__(self, protocol_type: Type[Protocol]):
        self._protocolo_type = protocol_type
        self._protocol_model = ProtocolService.create_protocol_model_from_type(protocol_type)
        self._experiment = ExperimentService.create_experiment_from_protocol_model(self._protocol_model)

    def get_protocol():
        pass
    
    async def run():
        pass