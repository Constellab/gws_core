# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List

from typing_extensions import TypedDict

from gws_core.process.process_types import ProcessConfigDict, ProcessSpecDict
from gws_core.protocol.protocol_layout import ProtocolLayoutDict


class ProtocolSpecDict(ProcessSpecDict):
    graph: Any


class ConnectorPartDict(TypedDict):
    node: str
    port: str


ConnectorDict = TypedDict('ConnectorDict', {'from': ConnectorPartDict, 'to': ConnectorPartDict})

InterfaceDict = TypedDict('InterfaceDict', {'name': str, 'from': ConnectorPartDict, 'to': ConnectorPartDict})


class ProtocolConfigDict(TypedDict):
    nodes: Dict[str, ProcessConfigDict]
    links: List[ConnectorDict]
    interfaces: dict
    outerfaces: dict
    layout: ProtocolLayoutDict
