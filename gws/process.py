# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import inspect
import zlib
from peewee import  IntegerField, CharField, ForeignKeyField

from .user import User
from .config import Config
from .logger import Error, Info
from .progress_bar import ProgressBar
from .viewable import Viewable
from .io import Input, Output, InPort, OutPort

class Process(Viewable):
    """
    Process class.

    :property input_specs: The specs of the input
    :type input_specs: dict
    :property output_specs: The specs of the output
    :type output_specs: dict
    :property config_specs: The specs of the config
    :type config_specs: dict
    """

    protocol_id = IntegerField(null=True, index=True)
    experiment_id = IntegerField(null=True, index=True)
    instance_name = CharField(null=True, index=True)
    created_by = ForeignKeyField(User, null=False, index=True, backref='+')
    config = ForeignKeyField(Config, null=False, index=True, backref='+')
    progress_bar = ForeignKeyField(ProgressBar, null=True, backref='+')

    input_specs: dict = {}
    output_specs: dict = {}
    config_specs: dict = {}

    title = None
    description = None

    is_instance_running = False
    is_instance_finished = False

    _experiment: 'Experiment' = None
    _protocol: 'Protocol' = None
    _file_store: 'FileStore' = None
    _input: Input = None
    _output: Output = None
    _max_progress_value = 100.0
    _is_singleton = False
    _is_removable = False
    _is_plug = False

    _table_name = 'gws_process'

    def __init__(self, *args, user=None, **kwargs):
        """
        Constructor
        """

        super().__init__(*args, **kwargs)

        if not self.title:
            self.title = self.full_classname().split(".")[-1]

        if not self.description:
            self.description = "This is the process class " + self.full_classname()

        self._input = Input(self)
        self._output = Output(self)

        if self.input_specs is None:
            self.input_specs = {}

        if self.output_specs is None:
            self.output_specs = {}

        if self.config_specs is None:
            self.config_specs = {}

        self._init_io()

        if not self.id:
            self.config = Config(specs=self.config_specs)
            self.config.save()

            self.progress_bar = ProgressBar(process_uri=self.uri, process_type=self.type)
            self.progress_bar.save()

            if not user:
                user = User.get_sysuser()

            if not isinstance(user, User):
                raise Error("gws.model.Process", "__init__", "The user must be an instance of User")

            self.created_by = user
            #self.is_protocol = isinstance(self, Protocol)

        if not self.instance_name:
            self.instance_name = self.uri

        self.save()


    def _init_io(self):
        from .service.model_service import ModelService

        if type(self) is Process:
            # Is the Base (Abstract) Process object => cannot set io
            return

        # intput
        for k in self.input_specs:
            self._input.create_port(k,self.input_specs[k])

        if not self.data.get("input"):
            self.data["input"] = {}

        for k in self.data["input"]:
            uri = self.data["input"][k]["uri"]
            type_ = self.data["input"][k]["type"]
            t = ModelService.get_model_type(type_)
            self._input.__setitem_without_check__(k, t.get(t.uri == uri))

        # output
        for k in self.output_specs:
            self._output.create_port(k,self.output_specs[k])

        if not self.data.get("output"):
            self.data["output"] = {}

        for k in self.data["output"]:
            uri = self.data["output"][k]["uri"]
            type_ = self.data["output"][k]["type"]
            t = ModelService.get_model_type(type_)
            self._output.__setitem_without_check__(k, t.get(t.uri == uri))

    # -- A --

    def archive(self, tf, archive_resources=True) -> bool:
        """
        Archive the process
        """

        if self.is_archived == tf:
            return True

        with self._db_manager.db.atomic() as transaction:
            if not super().archive(tf):
                return False

            self.config.archive(tf) #-> try to archive the config if possible!

            if archive_resources:
                for r in self.resources:
                    if not r.archive(tf):
                        transaction.rollback()
                        return False

        return True

    # -- C --

    @classmethod
    def create_process_type(cls):
        from .typing import ProcessType
        exist = ProcessType.select().where(ProcessType.model_type == cls.full_classname()).count()
        if not exist:
            pt = ProcessType(
                model_type = cls.full_classname(),
                root_model_type = "gws.process.Process"
            )
            pt.save()

    def create_experiment(self, study: 'Study', uri:str=None, user: 'User' = None):
        """
        Create an experiment using a protocol composed of this process

        :param study: The study in which the experiment is realized
        :type study: `gws.model.Study`
        :param study: The configuration of protocol
        :type study: `gws.model.Config`
        :return: The experiment
        :rtype: `gws.model.Experiment`
        """

        from .experiment import Experiment
        from .protocol import Protocol
        from .service.user_service import UserService

        proto = Protocol(processes={self.instance_name: self})
        if user is None:
            user = UserService.get_current_user()
            if user is None:
                raise Error("Process", "create_experiment", "A user is required")
        if uri:
            e = Experiment(uri=uri, protocol=proto, study=study, user=user)
        else:
            e = Experiment(protocol=proto, study=study, user=user)
        e.save()
        return e

    def create_source_zip(self):
        """
        Returns the zipped code source of the process
        """

        from .service.model_service import ModelService
        model_t = ModelService.get_model_type(self.type) #/:\ Use the true object type (self.type)
        source = inspect.getsource(model_t)
        return zlib.compress(source.encode())

    def check_before_task(self) -> bool:
        """
        This must be overloaded to perform custom check before running task.

        This method is systematically called before running the process task.
        If `False` is returned, the process task will not be called; otherwise, the task will proceed normally.

        :return: `True` if everything is OK, `False` otherwise. Defaults to `True`.
        :rtype: `bool`
        """

        return True

    # -- D --

    def disconnect(self):
        """
        Disconnect the input and output ports
        """

        self._input.disconnect()
        self._output.disconnect()

    # -- E --

    @property
    def experiment(self):
        if self._experiment:
            return self._experiment
        if self.experiment_id:
            from .experiment import Experiment
            self._experiment = Experiment.get_by_id(self.experiment_id)
        return self._experiment

    # -- G --

    def get_param(self, name: str) -> [str, int, float, bool]:
        """
        Returns the value of a parameter of the process config by its name.

        :return: The paremter value
        :rtype: [str, int, float, bool]
        """

        return self.config.get_param(name)

    def get_next_procs(self) -> list:
        """
        Returns the list of (right-hand side) processes connected to the IO ports.

        :return: List of processes
        :rtype: list
        """

        return self._output.get_next_procs()

    # -- H --

    # -- I --

    @property
    def is_running(self) -> bool:
        if not self.progress_bar:
            return False

        p = ProgressBar.get_by_id(self.progress_bar.id)
        return p.is_running


    @property
    def is_finished(self) -> bool:
        if not self.progress_bar:
            return False

        p = ProgressBar.get_by_id(self.progress_bar.id)
        return p.is_finished

    @property
    def is_ready(self) -> bool:
        """
        Returns True if the process is ready (i.e. all its ports are
        ready or it has never been run before), False otherwise.

        :return: True if the process is ready, False otherwise.
        :rtype: bool
        """

        return (not self.is_instance_running and not self.is_instance_finished) and self._input.is_ready

    @property
    def input(self) -> 'Input':
        """
        Returns input of the process.

        :return: The input
        :rtype: Input
        """

        from .service.model_service import ModelService

        if self._input.is_empty:
            for k in self.data["input"]:
                uri = self.data["input"][k]["uri"]
                type_ = self.data["input"][k]["type"]
                t = ModelService.get_model_type(type_)
                self._input[k] = t.get(t.uri == uri)

        return self._input

    def in_port(self, name: str) -> InPort:
        """
        Returns the port of the input by its name.

        :return: The port
        :rtype: InPort
        """
        if not isinstance(name, str):
            raise Error("gws.model.Process", "in_port", "The name of the input port must be a string")

        if not name in self._input._ports:
            raise Error("gws.model.Process", "in_port", f"The input port '{name}' is not found")

        return self._input._ports[name]

    # -- J --

    # -- L --

    def __lshift__(self, name: str) -> InPort:
        """
        Alias of :meth:`in_port`.
        Returns the port of the input by its name

        :return: The port
        :rtype: InPort
        """
        return self.in_port(name)

    # -- O --

    @property
    def output(self) -> 'Output':
        """
        Returns output of the process.

        :return: The output
        :rtype: Output
        """

        from .service.model_service import ModelService

        if self._output.is_empty:
            for k in self.data["output"]:
                uri = self.data["output"][k]
                type_ = self.data["output"][k]["type"]
                t = ModelService.get_model_type(type_)
                self._output[k] = t.get(t.uri == uri)

        return self._output

    def out_port(self, name: str) -> OutPort:
        """
        Returns the port of the output by its name.

        :return: The port
        :rtype: OutPort
        """
        if not isinstance(name, str):
            raise Error("gws.model.Process", "out_port", "The name of the output port must be a string")

        if not name in self._output._ports:
            raise Error("gws.model.Process", "out_port", f"The output port '{name}' is not found")

        return self._output._ports[name]

    # -- P --

    def param_exists(self, name: str) -> bool:
        """
        Test if a parameter exists

        :return: True if the parameter exists, False otherwise
        :rtype: `bool`
        """

        return self.config.param_exists(name)

    @property
    def protocol(self):
        if self._protocol:
            return self._protocol
        if self.protocol_id:
            from .protocol import Protocol
            self._protocol = Protocol.get_by_id(self.protocol_id)
        return self._protocol

    # -- R --

    @property
    def resources(self):
        from .resource import ProcessResource
        Qrel = ProcessResource.select().where(ProcessResource.process_id == self.id)
        Q = []
        for o in Qrel:
            Q.append(o.resource)

        return Q

    def _reset(self) -> bool:
        """
        Reset the process

        :return: Returns True if is process is successfully reset;  False otherwise
        :rtype: `bool`
        """

        if self.is_running:
            return False

        if self.experiment:
            if self.experiment.is_validated or self.experiment._is_running:
                return False

        self.progress_bar._reset()
        self._reset_io()
        return self.save()

    def _reset_io(self):
        self.input._reset()
        self.output._reset()
        self.data["input"] = {}
        self.data["output"] = {}

    async def _run(self):
        """
        Run the process and save its state in the database.
        """

        if not self.is_ready:
            return

        is_ok = self.check_before_task()
        if isinstance(is_ok, bool) and not is_ok:
            return

        try:
            await self._run_before_task()
            await self.task()
            await self._run_after_task()
        except Exception as err:
            self.progress_bar.stop(message = str(err))
            raise err

    async def _run_next_processes(self):
        self._output.propagate()
        aws  = []
        for proc in self._output.get_next_procs():
            aws.append( proc._run() )

        if len(aws):
            await asyncio.gather( *aws )

    async def _run_before_task( self, *args, **kwargs ):
        Info(f"Running {self.full_classname()} ...")

        self.is_instance_running = True
        self.is_instance_finished = False

        self.data["input"] = {}
        for k in self._input:
            if self._input[k]:  #-> check that an input resource exists (for optional input)
                if not self._input[k].is_saved():
                    self._input[k].save()

                self.data["input"][k] = {
                    "uri": self._input[k].uri,
                    "type": self._input[k].type
                }

        self.progress_bar.start(max_value=self._max_progress_value)
        self.save()

    async def _run_after_task( self, *args, **kwargs ):
        Info(f"Task of {self.full_classname()} successfully finished!")

        self.is_instance_running = False
        self.is_instance_finished = True
        self.progress_bar.stop()

        if not self._is_plug:
            res = self.output.get_resources()
            for k in res:
                if not res[k] is None:
                    res[k].experiment = self.experiment
                    res[k].process = self
                    res[k].save()

        if not self._output.is_ready:
            return

        from .protocol import Protocol
        if isinstance(self, Protocol):
            self.save(update_graph=True)

        self.data["output"] = {}
        for k in self._output:
            if self._output[k]: #-> check that an output resource exists (for optional outputs)
                self.data["output"][k] = {
                    "uri": self._output[k].uri,
                    "type": self._output[k].type
                }

        await self._run_next_processes()

    def __rshift__(self, name: str) -> OutPort:
        """
        Alias of :meth:`out_port`.

        Returns the port of the output by its name
        :return: The port
        :rtype: OutPort
        """
        return self.out_port(name)

    # -- S --

    def set_experiment(self, experiment):
        from .experiment import Experiment
        if not isinstance(experiment, Experiment):
            raise Error("gws.model.Process", "set_experiment", f"An instance of Experiment is required")
        if not experiment.id:
            if not experiment.save():
                raise Error("gws.model.Process", "set_experiment", f"Cannot save the experiment")
        if self.experiment_id and self.experiment_id != experiment.id:
            raise Error("gws.model.Process", "set_experiment", f"The protocol is already related to an experiment")
        self.experiment_id = experiment.id
        self.save()

    def set_input(self, name: str, resource: 'Resource'):
        """
        Sets the resource of an input port by its name.

        :param name: The name of the input port
        :type name: str
        :param resource: A reources to assign to the port
        :type resource: Resource
        """

        if not isinstance(name, str):
            raise Error("gws.model.Process", "set_input", "The name must be a string.")

        #if not not isinstance(resource, Resource):
        #    raise Error("gws.model.Process", "set_input", "The resource must be an instance of Resource.")

        self._input[name] = resource

    def set_config(self, config: 'Config'):
        """
        Sets the config of the process.

        :param config: A config to assign
        :type config: Config
        """

        self.config = config
        self.save()

    def set_param(self, name: str, value: [str, int, float, bool]):
        """
        Sets the value of a config parameter.

        :param name: Name of the parameter
        :type name: str
        :param value: A value to assign
        :type value: [str, int, float, bool]
        """

        self.config.set_param(name, value)
        self.config.save()

    # -- T --

    async def task(self):
        pass

    def to_json(self, *, shallow=False, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the process.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(**kwargs)
        _json["data"]["title"] = self.title
        _json["data"]["description"] = self.description
        _json["data"]["doc"] = inspect.getdoc(type(self))

        del _json["experiment_id"]
        del _json["protocol_id"]

        if "input" in _json["data"]:
            del _json["data"]["input"]

        if "output" in _json["data"]:
            del _json["data"]["output"]

        bare = kwargs.get("bare")
        if bare:
            _json["experiment"] = { "uri" : "" }
            _json["protocol"] = { "uri" : "" }
            _json["is_running"] = False
            _json["is_finished"] = False

            if shallow:
                _json["config"] = { "uri" : "" }
                _json["progress_bar"] = { "uri" : "" }
                #if _json["data"].get("graph"):
                #    del _json["data"]["graph"]
            else:
                _json["config"] = self.config.to_json(**kwargs)
                _json["progress_bar"] = self.progress_bar.to_json(**kwargs)
        else:
            _json["experiment"] = { "uri" : (self.experiment.uri if self.experiment_id else "") }
            _json["protocol"] = { "uri" : (self.protocol.uri if self.protocol_id else "") }
            _json["is_running"] = self.progress_bar.is_running
            _json["is_finished"] = self.progress_bar.is_finished

            if shallow:
                _json["config"] = { "uri" : self.config.uri }
                _json["progress_bar"] = { "uri" : self.progress_bar.uri }
                #if _json["data"].get("graph"):
                #    del _json["data"]["graph"]
            else:
                _json["config"] = self.config.to_json(**kwargs)
                _json["progress_bar"] = self.progress_bar.to_json(**kwargs)

        _json["input"] = self.input.to_json(**kwargs)
        _json["output"] = self.output.to_json(**kwargs)

        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
