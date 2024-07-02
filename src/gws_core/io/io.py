

from abc import abstractmethod
from typing import Dict, Generic, List, Type, TypeVar, final

from gws_core.io.dynamic_io import DynamicInputs, DynamicOutputs
from gws_core.io.io_dto import IODTO
from gws_core.io.io_spec import IOSpec
from gws_core.io.io_specs import InputSpecs, IOSpecs, IOSpecsType, OutputSpecs
from gws_core.resource.resource_set.resource_list_base import ResourceListBase

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.base import Base
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from .io_exception import ResourceNotCompatibleException
from .port import InPort, OutPort, Port

# For generic Port type
PortType = TypeVar('PortType', bound=Port)


class IO(Base, Generic[PortType]):
    """
    Base IO class. The IO class defines base functionalitie for the
    Input and Output classes. A IO is a set of ports.
    """

    _ports: Dict[str, PortType] = {}
    _type: IOSpecsType = None
    _additional_info: dict = None

    def __init__(self, type_: IOSpecsType = 'normal', additional_info: dict = None) -> None:
        self._ports = dict()
        self._type = type_
        if additional_info is None:
            additional_info = None
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

    def get_resource_models(self) -> Dict[str, ResourceModel]:
        """Get the resource_model of a port
        """
        resource_models: Dict[str, ResourceModel] = {}
        for port_name, port in self._ports.items():
            if port.resource_model:
                resource_models[port_name] = port.resource_model
        return resource_models

    def get_resource_model(self, port_name: str) -> ResourceModel:
        """Get the resource_model of a port
        """
        port: PortType = self.get_port(port_name)
        return port.resource_model

    def has_resource_model(self, resource_model_id: str, include_sub_resouces: bool = False) -> bool:
        """_summary_
        return true if one of the ports contain the resource model

        :param resource_model_id: resource model id to check
        :type resource_model_id: str
        :param include_sub_resouces: if True, it also check if provided resource is inside ResourceListBase, defaults to False
        :type include_sub_resouces: bool, optional
        :return: True if the resource model is in the ports
        :rtype: bool
        """
        for port in self._ports.values():
            if port.resource_model:
                if port.resource_model.id == resource_model_id:
                    return True

                if include_sub_resouces:
                    resource = port.get_resource(new_instance=False)
                    if isinstance(resource, ResourceListBase) and resource.has_resource_model(resource_model_id):
                        return True

        return False

    ################################################### JSON ########################################

    @classmethod
    def load_from_json(cls, io_json: dict) -> 'IO':
        return cls.load_from_dto(IODTO.from_json(io_json))

    @classmethod
    def load_from_dto(cls, io_dto: IODTO) -> 'IO':
        io: IO = cls(type_=io_dto.type, additional_info=io_dto.additional_info)

        # To create an InPort or OutPort
        port_type: Type[PortType] = io._get_port_type()
        for key, port_dto in io_dto.ports.items():

            port: PortType = port_type.load_from_dto(port_dto, key)

            if port_dto.resource_id:
                resource_model: ResourceModel = ResourceModel.get_by_id(port_dto.resource_id)
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

    def to_json(self) -> dict:
        return self.to_dto().to_json_dict()

    def to_dto(self) -> IODTO:
        io_dto = IODTO(
            ports={key: port.to_dto() for key, port in self._ports.items()},
            type=self._type,
            additional_info=self._additional_info
        )

        return io_dto

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
        return io_specs

    def get_specs_as_dict(self) -> dict:
        specs = self.get_specs().get_specs()
        io_specs = {}
        for key, value in specs.items():
            io_specs[key] = value.to_dto().to_json_dict()

        return {"specs": io_specs}


@final
class Inputs(IO[InPort]):
    """
    Input class
    """

    def _get_port_type(self) -> Type[InPort]:
        return InPort

    def _build_specs(self, specs: Dict[str, IOSpec]) -> IOSpecs:
        if self.is_dynamic:
            return DynamicInputs.from_dto(specs, self._additional_info)
        return InputSpecs(specs)


@final
class Outputs(IO[OutPort]):
    """
    Output class
    """

    def _get_port_type(self) -> Type[OutPort]:
        return OutPort

    def _build_specs(self, specs: Dict[str, IOSpec]) -> IOSpecs:
        if self.is_dynamic:
            return DynamicOutputs.from_dto(specs, self._additional_info)
        return OutputSpecs(specs)
