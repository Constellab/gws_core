# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, ProcessableSpec, Protocol,
                      ProtocolDecorator, RobotCreate, RobotEat, RobotMove,
                      RobotWait)

# File for Tests containing examples of protocols


@ProtocolDecorator("TestSimpleProtocol")
class TestSimpleProtocol(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        p0: ProcessableSpec = self.add_process(RobotCreate, 'p0')
        p1: ProcessableSpec = self.add_process(RobotMove, 'p1')
        p2: ProcessableSpec = self.add_process(RobotEat, 'p2')
        p3: ProcessableSpec = self.add_process(RobotMove, 'p3')
        p4: ProcessableSpec = self.add_process(RobotMove, 'p4')
        p5: ProcessableSpec = self.add_process(RobotEat, 'p5')
        p_wait: ProcessableSpec = self.add_process(RobotWait, 'p_wait')

        self.add_connectors([
            (p0 >> 'robot', p1 << 'robot'),
            (p1 >> 'robot', p2 << 'robot'),
            (p2 >> 'robot', p_wait << 'robot'),
            (p_wait >> 'robot', p3 << 'robot'),
            (p3 >> 'robot', p4 << 'robot'),
            (p2 >> 'robot', p5 << 'robot')
        ])


@ProtocolDecorator("TestSubProtocol")
class TestSubProtocol(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        p1: ProcessableSpec = self.add_process(RobotMove, 'p1')
        p2: ProcessableSpec = self.add_process(RobotEat, 'p2')
        p3: ProcessableSpec = self.add_process(RobotMove, 'p3')
        p4: ProcessableSpec = self.add_process(RobotMove, 'p4')
        p_wait: ProcessableSpec = self.add_process(RobotWait, 'p_wait')

        self.add_connectors([
            (p1 >> 'robot', p2 << 'robot'),
            (p2 >> 'robot', p_wait << 'robot'),
            (p_wait >> 'robot', p3 << 'robot'),
            (p2 >> 'robot', p4 << 'robot')
        ])

        self.add_interface('robot',  p1, 'robot'),
        self.add_outerface('robot',  p2, 'robot'),


@ProtocolDecorator("TestNestedProtocol")
class TestNestedProtocol(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        p0: ProcessableSpec = self.add_process(RobotCreate, 'p0')
        p5: ProcessableSpec = self.add_process(RobotEat, 'p5')
        mini_proto: ProcessableSpec = self.add_process(TestSubProtocol, 'mini_proto')

        self.add_connectors([
            (p0 >> 'robot', mini_proto << 'robot'),
            (mini_proto >> 'robot', p5 << 'robot')
        ])
