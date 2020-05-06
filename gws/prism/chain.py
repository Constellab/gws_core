#
# Python GWS chain
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#

from gws.prism.model import Process, Resource

class Chain:
    _input: Resource = None
    _output: Resource = None
    _processes = []

    def __init__(self, *args):
        self._input = None
        self._output = None
        self._processes = []

        for proc in args:
            if proc in self._processes:
                raise Exception("Chain", "__init__", "Process duplicates are not allowed")
            else:
                self._processes.append(proc)

    def at(self, index: int) -> Process:
        return self._processes[index]

    def append(self, process: Process):
        self._processes.append(process)

    @property
    def input(self) -> 'Process':
        return self._input

    def insert(self, index: int, process: Process):
        self._processes.insert(index, process)

    @property
    def output(self) -> 'Process':
        return self._output

    def pop(self, index: int, default = None) -> 'Process':
        return self._processes.pop(index, default)

    def run(self, params={}):
        """ 
            Use input model to create output model
        """
        self._processes[0].set_input(self._input)
        self._processes[0].run(params)

    def set_input(self, input: Resource):
        self._input = input
    