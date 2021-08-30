# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import inspect
import zlib
from typing import Dict, Type

from gws_core.resource.resource import Resource

from ..config.config_params import ConfigParams
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..model.typing_manager import TypingManager
from ..model.typing_register_decorator import TypingDecorator
from ..process.process_io import ProcessInputs, ProcessOutputs
from ..processable.processable_model import ProcessableModel
from ..resource.resource_data import ResourceData
from ..resource.resource_model import ResourceModel
from .process import Process


@TypingDecorator(unique_name="Process", object_type="GWS_CORE", hide=True)
class ProcessModel(ProcessableModel):
    """
    Process class.

    :property input_specs: The specs of the input
    :type input_specs: dict
    :property output_specs: The specs of the output
    :type output_specs: dict
    :property config_specs: The specs of the config
    :type config_specs: dict
    """

    _is_plug = False

    _table_name = 'gws_process'  # is locked for all processes

    def __init__(self, *args, **kwargs):
        """
        Constructor
        """

        super().__init__(*args, **kwargs)

        if self.processable_typing_name is not None:
            self._init_io()

    def _init_io(self):
        process_type: Type[Process] = self._get_processable_type()

        # create the input ports from the Process input specs
        for k in process_type.input_specs:
            self._input.create_port(k, process_type.input_specs[k])

        # set the resources to the ports
        self._init_input_from_data()

        # create the output ports from the Process output specs
        for k in process_type.output_specs:
            self._output.create_port(k, process_type.output_specs[k])

        # set the resources to the ports
        self._init_output_from_data()

    # -- C --

    def create_source_zip(self):
        """
        Returns the zipped code source of the process
        """

        # /:\ Use the true object type (self.type)
        model_t: Type[ProcessModel] = TypingManager.get_type_from_name(
            self.processable_typing_name)
        source = inspect.getsource(model_t)
        return zlib.compress(source.encode())

    def set_process_type(self, typing_name: str) -> None:
        self.processable_typing_name = typing_name
        self._init_io()

    # -- D --

    def _create_processable_instance(self) -> Process:
        return self._get_processable_type()()

    async def _run(self) -> None:
        """
        Run the process and save its state in the database.
        """
        # Create the process instance to run the task
        process: Process = self._create_processable_instance()

        # Get simpler object for to run the task
        config_params: ConfigParams = self.config.get_and_check_params()
        process_inputs: ProcessInputs = self.input.get_and_check_process_inputs()

        is_ok = process.check_before_task(
            config=config_params, inputs=process_inputs)

        # TODO qu'est-ce qu'on fait quand c'est false ? Pas de message d'erreur ?  On raise une exception ?
        if isinstance(is_ok, bool) and not is_ok:
            return
        try:
            await self._run_before_task()
            # run the task
            await self._run_task(process=process, config_params=config_params, process_inputs=process_inputs)
            await self._run_after_task()
        except Exception as err:
            self.progress_bar.stop(message=str(err))
            raise err

    async def _run_task(self, process: Process, config_params: ConfigParams, process_inputs: ProcessInputs) -> None:
        """
        Run the process and save its state in the database.
        """

        # Run the process task
        process_output: ProcessOutputs = await process.task(config=config_params, inputs=process_inputs, progress_bar=self.progress_bar)

        if process_output is None:
            process_output = {}

        if not isinstance(process_output, dict):
            raise BadRequestException('The process output is not a dictionary')

        for key, port in self.output.ports.items():
            resource_model: ResourceModel

            # If the resource for the output port was provided
            if key in process_output:

                resource: Resource = process_output[key]

                if not isinstance(resource, Resource):
                    raise BadRequestException(
                        f"The output '{key}' of type '{type(resource)}' is not a resource. It must extend the Resource class")

                # Get the type of resource model to create for this resource
                resource_model_type: Type[ResourceModel] = resource.get_resource_model_type()
                if not issubclass(resource_model_type, ResourceModel):
                    raise BadRequestException(
                        f"The method get_resource_model_type of resource {resource.classname()} did not return a type that extend ResourceModel")
                # create the resource model from the resource
                resource_model = resource_model_type.from_resource(resource)

            else:
                resource_model = None

            # save the resource model into the output's port (even if it's None)
            port.resource_model = resource_model

    async def _run_after_task(self):

        if not self._is_plug:
            # Save the generated resource
            res: Dict[str, ResourceModel] = self.output.get_resources()
            for resource in res.values():
                if resource is not None:
                    resource.experiment = self.experiment
                    resource.process = self
                    resource.save()
        await super()._run_after_task()

    def is_protocol(self) -> bool:
        return False

    def save_full(self) -> None:
        self.config.save()
        self.progress_bar.save()
        self.save()

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model.
        :return: The representation
        :rtype: `dict`
        """
        # TODO a tester, besoin du   {**_json, **self.data} ?
        _json: dict = super().data_to_json(deep=deep)

        return {**_json, **self.data}
