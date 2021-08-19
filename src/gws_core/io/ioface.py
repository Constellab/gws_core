from typing import final

from gws_core.resource.resource import Resource

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .port import InPort, OutPort, Port


class IOface:
    name: str = None
    source_port: Port = None
    target_port: Port = None

    def __init__(self, name: str, source_port: Port, target_port: Port):
        if not isinstance(source_port, Port):
            raise BadRequestException("The source port must be a port")

        if not isinstance(target_port, Port):
            raise BadRequestException("The target port must be a port")

        self.name = name
        self.source_port = source_port
        self.target_port = target_port

    # -- D --

    def disconnect(self):
        """
        Disconnect the IOFace
        """

        if self.source_port:
            self.source_port.disconnect()

        if self.target_port:
            self.target_port.disconnect()

    # -- R --

    def reset(self):
        if self.source_port:
            self.source_port.reset()

        if self.target_port:
            self.target_port.reset()

    # -- T --

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        r_uri = ""
        r_typing_name = ""
        if self.source_port.resource:
            r_uri = self.source_port.resource.uri
            r_typing_name = self.source_port.resource.typing_name

        return {
            "name": self.name,
            "from": {
                "node": self.source_port.process.instance_name,
                "port": self.source_port.name,
            },
            "to": {
                "node": self.target_port.process.instance_name,
                "port": self.target_port.name,
            },
            "resource": {
                "uri": r_uri,
                "typing_name": r_typing_name
            }
        }


@final
class Interface(IOface):
    source_port: InPort = None
    target_port: InPort = None

    def __init__(self, name: str, source_port: InPort, target_port: InPort):

        if not isinstance(source_port, InPort):
            raise BadRequestException("The source port must be an input port")

        if not isinstance(target_port, InPort):
            raise BadRequestException("The target port must be an input port")

        super().__init__(name, source_port, target_port)

    # -- S --

    def set_resource(self, resource: 'Resource'):
        self.source_port.resource = resource
        self.target_port.resource = resource

    # -- V -

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        _json = super().to_json(deep=deep, **kwargs)
        _json["from"]["node"] = ":parent:"
        return _json


@final
class Outerface(IOface):
    source_port: OutPort = None
    target_port: OutPort = None

    def __init__(self, name: str, source_port: OutPort, target_port: OutPort):

        if not isinstance(source_port, OutPort):
            raise BadRequestException("The source port must be an output port")

        if not isinstance(target_port, OutPort):
            raise BadRequestException("The target port must be an output port")

        super().__init__(name, source_port, target_port)

    # -- G --

    def get_resource(self) -> Resource:
        return self.source_port.resource

    # -- V --

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        _json = super().to_json(deep=deep, **kwargs)
        _json["to"]["node"] = ":parent:"
        return _json
