# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from abc import abstractmethod
from typing import Dict, Generic, List, Type, TypedDict, TypeVar, final

from gws_core.io.dynamic_io import DynamicInputs, DynamicOutputs
from gws_core.io.io_spec import IOSpec
from gws_core.io.io_specs import InputSpecs, IOSpecs, IOSpecsType, OutputSpecs

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.base import Base
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from .io_exception import ResourceNotCompatibleException
from .port import InPort, OutPort, Port, PortDict


class IODict(TypedDict):
    """IODict type
    """
    ports: Dict[str, PortDict]
    type: IOSpecsType
    additional_info: dict


# For generic Port type
PortType = TypeVar('PortType', bound=Port)


####################################################################
#
# IO class
#
# ####################################################################
class IO(Base, Generic[PortType]):
    """
    Base IO class. The IO class defines base functionalitie for the
    Input and Output classes. A IO is a set of ports.
    """

    _ports: Dict[str, PortType] = {}
    _type: IOSpecsType = None
    _additional_info: dict = {}

    def __init__(self, type_: IOSpecsType = 'normal', additional_info: dict = None) -> None:
        self._ports = dict()
        self._type = type_
        if additional_info is None:
            additional_info = {}
        self._additional_info = additional_info

    @property
    def is_ready(self) -> bool:
        """
        Returns True if the IO is ready (i.e. all its ports are ready), False otherwise.

        :return: True if the IO is ready, False otherwise.
        :rtype: bool
        """

        for port in self._ports.values():
            if not port.is_ready:
                return False

        return True

    @property
    def is_dynamic(self) -> bool:
        return self._type == 'dynamic'

    def reset(self) -> None:
        for port in self._ports.values():
            port.reset()

    ################################################### PORTS ########################################

    @property
    def ports(self) -> Dict[str, PortType]:
        """
        Returns the list of ports.

        :return: List of port
        :rtype: list
        """

        return self._ports

    def create_port(self, name: str, resource_spec: IOSpec) -> PortType:
        """
        Creates a port.

        :param name: Name of the port
        :type name: str
        :param resource_types: The expected type of the resource of the port
        :type resource_types: type
        """

        port_type: Type[PortType] = self._get_port_type()
        port: PortType = port_type(name, resource_spec)
        self.add_port(name, port)
        return port

    def update_port(self, name: str, resource_spec: IOSpec) -> PortType:
        """
        Update a port.

        :param name: Name of the port
        :type name: str
        :param resource_types: The expected type of the resource of the port
        :type resource_types: type
        """
        self._check_port_name(name)

        return self.create_port(name, resource_spec)

    def add_port(self, name: str, port: PortType) -> None:
        if not isinstance(name, str):
            raise BadRequestException(
                "Invalid port specs. The port name must be a string")
        self._ports[name] = port

    @abstractmethod
    def _get_port_type(self) -> Type[PortType]:
        pass

    @abstractmethod
    def _build_specs(self, specs: Dict[str, IOSpec]) -> IOSpecs:
        pass

    def get_port_names(self) -> List[str]:
        """
        Returns the names of all the ports.

        :return: List of names
        :rtype: list
        """

        return list(self._ports.keys())

    def get_port(self, port_name: str) -> PortType:
        """
        Returns the resources of all the ports.

        :return: List of resources
        :rtype: list
        """
        self._check_port_name(port_name)
        return self._ports[port_name]

    def port_exists(self, name: str) -> bool:
        return name in self._ports

    def remove_port(self, port_name: str) -> None:
        self._check_port_name(port_name)
        del self._ports[port_name]

    def _check_port_name(self, name) -> None:

        if not isinstance(name, str):
            raise BadRequestException(
                f"The port name must be a string. Actual value: '{name}'")

        if not self.port_exists(name):
            raise BadRequestException(
                f"{self.classname()} port '{name}' not found")

    ################################################### RESOURCE ########################################
    def get_resources(self, new_instance: bool = False) -> Dict[str, Resource]:
        """
        Returns the resources of all the ports to be used for the input of a task.
        """
        resources: Dict[str, Resource] = {}

        # for normal IO, add the resource with key = port name
        for key, port in self._ports.items():
            resources[key] = port.get_resource(new_instance)
        return resources

    def set_resource_model(self, port_name: str, resource_model: ResourceModel) -> None:
        """Set the resource_model of a port
        """
        port: PortType = self.get_port(port_name)

        resource_type: Type[Resource] = type(resource_model.get_resource())
        if not port.resource_type_is_compatible(resource_type):
            raise ResourceNotCompatibleException(port_name=port_name, resource_type=resource_type,
                                                 spec=port.resource_spec)

        port.resource_model = resource_model

    def get_resource_model(self, port_name: str) -> ResourceModel:
        """Get the resource_model of a port
        """
        port: PortType = self.get_port(port_name)
        return port.resource_model

    def has_resource_model(self, resource_model_id: str) -> bool:
        """return true if one of the ports contain the resource model
        """
        for port in self._ports.values():
            if port.resource_model and port.resource_model.id == resource_model_id:
                return True
        return False

    ################################################### JSON ########################################

    @classmethod
    def load_from_json(cls, io_json: IODict) -> 'IO':
        io: IO = cls(type_=io_json.get('type', 'normal'), additional_info=io_json.get('additional_info', {}))
        port_dict: dict = io_json.get('ports', {})

        # To create an InPort or OutPort
        port_type: Type[PortType] = io._get_port_type()
        for key, port_dict in port_dict.items():

            port: PortType = port_type.load_from_json(port_dict, key)

            if port_dict["resource_id"]:
                resource_model: ResourceModel = ResourceModel.get_by_id(port_dict["resource_id"])
                port.resource_model = resource_model

            io.add_port(key, port)

        return io

    @classmethod
    def load_from_specs(cls, specs: IOSpecs) -> 'IO':
        io: IO = cls(type_=specs.get_type(), additional_info=specs.get_additional_info())

        # create the input ports from the Task input specs
        for key, value in specs.get_specs().items():
            io.create_port(key,  value)

        return io

    def to_json(self) -> IODict:
        _json: IODict = {
            "ports": {},
            "type": self._type,
            "additional_info": self._additional_info
        }

        for key, port in self._ports.items():
            _json["ports"][key] = port.to_json()

        return _json

    def get_specs(self) -> IOSpecs:
        """
        Returns the specs of all the ports.

        :return: List of specs
        :rtype: list
        """

        specs: Dict[str, IOSpec] = {}

        for key, port in self._ports.items():
            specs[key] = port.resource_spec

        io_specs = self._build_specs(specs)
        io_specs.set_additional_info(self._additional_info)
        return io_specs


# ####################################################################
#
# Input class
#
# ####################################################################


@final
class Inputs(IO[InPort]):
    """
    Input class
    """

    def _get_port_type(self) -> Type[InPort]:
        return InPort

    def _build_specs(self, specs: Dict[str, IOSpec]) -> IOSpecs:
        if self.is_dynamic:
            return DynamicInputs(specs)
        return InputSpecs(specs)


# ####################################################################
#
# Output class
#
# ####################################################################


@final
class Outputs(IO[OutPort]):
    """
    Output class
    """

    def _get_port_type(self) -> Type[OutPort]:
        return OutPort

    def _build_specs(self, specs: Dict[str, IOSpec]) -> IOSpecs:
        if self.is_dynamic:
            return DynamicOutputs(specs)
        return OutputSpecs(specs)
