
from __future__ import annotations

from abc import abstractmethod
from typing import Dict, List, Type, TypedDict, final

from peewee import Tuple

from ..config.config_types import ConfigParams, ConfigParamsDict, ConfigSpecs
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..model.typing_register_decorator import typing_registrator
from ..process.process import Process
from .protocol_spec import (ConnectorPartSpec, ConnectorSpec, InterfaceSpec,
                            ProcessSpec)

# Typing names generated for the class Protocol
CONST_PROTOCOL_TYPING_NAME = "PROTOCOL.gws_core.Protocol"


class ProtocolCreateConfig(TypedDict):
    process_specs: Dict[str, ProcessSpec]

    connectors: List[ConnectorSpec]

    interfaces: Dict[str, InterfaceSpec]
    outerfaces: Dict[str, InterfaceSpec]


@typing_registrator(unique_name="Protocol", object_type="PROTOCOL", hide=True)
class Protocol(Process):

    # Config spec of the process at the class level
    config_specs: ConfigSpecs = {}

    _process_specs: Dict[str, ProcessSpec]
    _connectors: List[ConnectorSpec]
    _interfaces: Dict[str, InterfaceSpec]
    _outerfaces: Dict[str, InterfaceSpec]

    @final
    def __init__(self) -> None:
        super().__init__()
        self._process_specs = {}
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
            "process_specs": self._process_specs,
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
        create: processSpec = self.register_process(RobotCreate, "create")
        move: processSpec = self.register_process(RobotMove, "move")
        eat: processSpec = self.register_process(RobotEat, "eat")


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
    def add_process(self, process_type: Type[Process], instance_name: str,
                    config_params: ConfigParamsDict = None) -> ProcessSpec:
        """Add a process to this protocol. The process_type can be a task or a protocol

        :param process_type: [description]
        :type process_type: Type[Process]
        :param instance_name: [description]
        :type instance_name: str
        :param config_params: [description], defaults to None
        :type config_params: ConfigParamsDict, optional
        :raises BadRequestException: [description]
        :return: [description]
        :rtype: ProcessSpec
        """

        # Check if a process with the same instance name was registered
        if instance_name in self._process_specs:
            spec: ProcessSpec = self._process_specs[instance_name]
            raise BadRequestException(
                f"Can't add the process {process_type.classname()} to the protocol. A process ({spec.process_type.classname()}) already exist with the same instance name '{instance_name}'.")

        # Create the process type wrapper
        process_spec: ProcessSpec = ProcessSpec(
            instance_name=instance_name, process_type=process_type)

        # Set configuration if defined
        if config_params:
            process_spec.set_params(config_params)

        # save the process spec in the dict
        self._process_specs[instance_name] = process_spec

        # return the type wrapper
        return self._process_specs[instance_name]

    @final
    def add_connectors(self, connections: List[Tuple[ConnectorPartSpec,  ConnectorPartSpec]]) -> None:
        """
        Add the connexion between processes of the protocol
        self.add_connectors([
            (create >> 'robot', move << 'robot'),
            (move >> 'robot', eat << 'robot'),
        ])
        :param connections: [description]
        :type connections: List[Tuple[ConnectorPartSpec,  ConnectorPartSpec]]
        """

        for connection in connections:
            self.add_connector(connection[0], connection[1])

    @final
    def add_connector(self, from_part: ConnectorPartSpec, to_part: ConnectorPartSpec) -> None:
        """ Add the connexion between 2 processes of the protocol
        self.add_connector(create >> 'robot', move << 'robot')

        :param from_part: [description]
        :type from_part: ConnectorPartSpec
        :param to_part: [description]
        :type to_part: ConnectorPartSpec
        """
        self._connectors.append({
            "from_process": from_part["process_instance_name"],
            "from_port": from_part["port_name"],
            "to_process": to_part["process_instance_name"],
            "to_port": to_part["port_name"]
        })

    @final
    def add_interface(self, name: str, from_process: ProcessSpec, process_input_name: str) -> None:
        """Add an interface to link an input of the protocol to the input of one of the protocol's process

        :param name: name of the interface
        :type name: str
        :param from_process: process that will be plugged to the interface
        :type from_process: IProcess
        :param process_input_name: name of the process input to plug
        :type process_input_name: str
        """

        # Check if the interface was already set
        if name in self._interfaces:
            raise BadRequestException(
                f"The interface with name '{name}' was already set.")

        self._interfaces[name] = {
            "process_instance_name": from_process.instance_name,
            "port_name": process_input_name
        }

    @final
    def add_outerface(self, name: str, to_process: ProcessSpec, process_output_name: str) -> None:
        """Add an outerface to link the output of one of the protocol's process to the output of the protocol

        :param name: name of the interface
        :type name: str
        :param from_process: process that will be plugged to the interface
        :type from_process: IProcess
        :param process_ouput_name: name of the process output to plug
        :type process_ouput_name: str
        """

        # Check if the interface was already set
        if name in self._outerfaces:
            raise BadRequestException(
                f"The outerface with name '{name}' was already set.")

        self._outerfaces[name] = {
            "process_instance_name": to_process.instance_name,
            "port_name": process_output_name
        }
