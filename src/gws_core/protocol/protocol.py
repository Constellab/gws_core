
from __future__ import annotations

from abc import abstractmethod
from typing import Dict, List, Type, TypedDict, final

from peewee import Tuple

from ..config.config_params import ConfigParams
from ..config.config_spec import ConfigSpecs, ConfigValues
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..model.typing_register_decorator import typing_registrator
from ..processable.processable import Processable
from .protocol_spec import (ConnectorPartSpec, ConnectorSpec, InterfaceSpec,
                            ProcessableSpec)

# Typing names generated for the class Process
CONST_PROTOCOL_TYPING_NAME = "PROTOCOL.gws_core.Protocol"


class ProtocolCreateConfig(TypedDict):
    processable_specs: Dict[str, ProcessableSpec]

    connectors: List[ConnectorSpec]

    interfaces: Dict[str, InterfaceSpec]
    outerfaces: Dict[str, InterfaceSpec]


@typing_registrator(unique_name="Protocol", object_type="PROTOCOL", hide=True)
class Protocol(Processable):

    # Config spec of the processable at the class level
    config_specs: ConfigSpecs = {}

    _processable_specs: Dict[str, ProcessableSpec]
    _connectors: List[ConnectorSpec]
    _interfaces: Dict[str, InterfaceSpec]
    _outerfaces: Dict[str, InterfaceSpec]

    @final
    def __init__(self) -> None:
        super().__init__()
        self._processable_specs = {}
        self._connectors = []
        self._interfaces = {}
        self._outerfaces = {}

    @final
    def get_create_config(self) -> ProtocolCreateConfig:
        """DO NOT OVERIDE
        This methdo return the parameters to create the protocol

        :return: [description]
        :rtype: ProtocolCreateConfig
        """
        return {
            "processable_specs": self._processable_specs,
            "connectors": self._connectors,
            "interfaces": self._interfaces,
            "outerfaces": self._outerfaces,
        }

    @abstractmethod
    def configure_protocol(self, config_params: ConfigParams) -> None:
        """Extend this method to configure the protocol (
        In this method you can reate sub process, add connectors and configure interface and outerface

        Here is a simpe exemple to configure a protocol

        # Add the processes
        create: ProcessableSpec = self.register_process(RobotCreate, "create")
        move: ProcessableSpec = self.register_process(RobotMove, "move")
        eat: ProcessableSpec = self.register_process(RobotEat, "eat")


        # Add the connexion between processes
        self.add_connectors([
            (create >> 'robot', move << 'robot'),
            (move >> 'robot', eat << 'robot'),
        ])

        # Configure protocol interface and outerfaces
        self.add_interface('robot', move_1, 'robot')
        self.add_outerface('robot', eat_2, 'robot')


        :param config_params: [description]
        :type config_params: ConfigParams
        """
        pass

    @final
    def add_process(self, processable_type: Type[Processable], instance_name: str,
                    config_values: ConfigValues = None) -> ProcessableSpec:
        # Check if a process with the same instance name was registered
        if instance_name in self._processable_specs:
            process_type: ProcessableSpec = self._processable_specs[instance_name]
            raise BadRequestException(
                f"Can't add the process {processable_type.classname()} to the protocol. A process ({process_type.processable_type.classname()}) already exist with the same instance name '{instance_name}'.")

        # Create the processable type wrapper
        processable_spec: ProcessableSpec = ProcessableSpec(
            instance_name=instance_name, processable_type=processable_type)

        # Set configuration if defined
        if config_values:
            processable_spec.configure_all(config_values)

        # save the process spec in the dict
        self._processable_specs[instance_name] = processable_spec

        # return the type wrapper
        return self._processable_specs[instance_name]

    @final
    def add_connectors(self, connections: List[Tuple[ConnectorPartSpec,  ConnectorPartSpec]]) -> None:
        for connection in connections:
            self.add_connector(connection[0], connection[1])

    @final
    def add_connector(self, from_part: ConnectorPartSpec, to_part: ConnectorPartSpec) -> None:
        self._connectors.append({
            "from_processable": from_part["processable_instance_name"],
            "from_port": from_part["port_name"],
            "to_processable": to_part["processable_instance_name"],
            "to_port": to_part["port_name"]
        })

    @final
    def add_interface(self, name: str, from_processable: ProcessableSpec, processable_output_name: str) -> None:
        # Check if the interface was already set
        if name in self._interfaces:
            raise BadRequestException(
                f"The interface with name '{name}' was already set.")

        self._interfaces[name] = {
            "processable_instance_name": from_processable.instance_name,
            "port_name": processable_output_name
        }

    @final
    def add_outerface(self, name: str, to_processable: ProcessableSpec, processable_output_name: str) -> None:
        # Check if the interface was already set
        if name in self._outerfaces:
            raise BadRequestException(
                f"The outerface with name '{name}' was already set.")

        self._outerfaces[name] = {
            "processable_instance_name": to_processable.instance_name,
            "port_name": processable_output_name
        }
