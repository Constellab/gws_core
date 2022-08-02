# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from importlib.resources import Resource

from gws_core.core.decorator.transaction import transaction
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.experiment.experiment_enums import ExperimentType
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.process.process_interface import IProcess
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.task.action.actions_manager import ActionsManager
from gws_core.task.action.action import Action
from gws_core.task.action.actions_task import ActionsTask
from gws_core.task.plug import Sink


class ActionService():

    ACTION_PROCESS_INSTANCE_NAME: str = 'action'

    @classmethod
    async def create_and_run_action_experiment(cls, resource_model_id: str) -> ResourceModel:

        # Get and check the resource id
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_model_id)

        # Create an experiment containing 1 source, X transformers task , 1 sink
        experiment: IExperiment = IExperiment(
            None, title=f"{resource_model.name} actions", type_=ExperimentType.ACTIONS)

        # add the action process
        action_process: IProcess = experiment.get_protocol().add_process(ActionsTask, cls.ACTION_PROCESS_INSTANCE_NAME, {})

        # create the source for the resource_model_id connected to the action process
        experiment.get_protocol().add_source(
            'source', resource_model_id, action_process << ActionsTask.source_input_name)

        # create the action resource
        action_resource: ResourceModel = ResourceModel.save_from_resource(ActionsManager(), ResourceOrigin.ACTIONS)

        # create the source for the new action_resource connected to the action process
        experiment.get_protocol().add_source('action_source', action_resource.id,
                                             action_process << ActionsTask.actions_input_name)

        # create the sink for the new action_resource connected to the action process
        experiment.get_protocol().add_sink('sink', action_process >> ActionsTask.target_output_name)

        #  run the experiment
        try:
            await experiment.run()
        except Exception as exception:
            # delete experiment if there was an error
            experiment.delete()
            action_resource.delete_instance()
            raise exception

        # return the resource model of the sink process
        return experiment.get_experiment_model().protocol_model.get_process('sink').inputs.get_resource_model(Sink.input_name)

    @classmethod
    @transaction()
    def execute_action(cls, resource_model_id: str, action_typing_name: str, action_params: dict) -> ResourceModel:

        # Get and check the resource id
        result_resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_model_id)
        result_resource: Resource = result_resource_model.get_resource()

        if result_resource_model.origin != ResourceOrigin.ACTIONS:
            raise Exception('The resource is not an action')

        action_resource_model = cls._get_actions_of_result_resource(result_resource_model)
        action_manager: ActionsManager = action_resource_model.get_resource()

        # create the new action
        new_action: Action = ActionsManager.instantiate_action(action_typing_name, action_params)

        # execute the action on the result resource
        result_resource = new_action.execute(result_resource)

        # update the resource model, and save
        cls._update_resource_model(result_resource_model, result_resource)

        # update the action resource model, and save
        action_manager.add_action(new_action)
        cls._update_resource_model(action_resource_model, action_manager)

        return result_resource_model

    @classmethod
    @transaction()
    def undo_last_action(cls, resource_model_id: str) -> ResourceModel:
        # Get and check the resource id
        result_resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_model_id)
        result_resource: Resource = result_resource_model.get_resource()

        if result_resource_model.origin != ResourceOrigin.ACTIONS:
            raise Exception('The resource is not an action')

        action_resource_model = cls._get_actions_of_result_resource(result_resource_model)
        action_manager: ActionsManager = action_resource_model.get_resource()

        # get the last action
        last_action: Action = action_manager.pop_action()

        if not last_action.is_reversible:
            raise BadRequestException('The last action cannot be undone')

        # undo the last action on the result resource
        result_resource = last_action.undo(result_resource)

        # update the resource model, and save
        cls._update_resource_model(result_resource_model, result_resource)

        # update the action resource model, and save
        cls._update_resource_model(action_resource_model, action_manager)

        return result_resource_model

    @classmethod
    def _update_resource_model(cls, resource_model: ResourceModel, resource: Resource) -> ResourceModel:
        # remove the kv_store to create a new one with the data
        resource_model.remove_kv_store()
        resource_model.receive_fields_from_resource(resource)
        return resource_model.save()

    @classmethod
    def _get_actions_of_result_resource(cls, result_resource_model: ResourceModel) -> ResourceModel:
        """ Method to retrieve the ActionsManager resource model from the result
            resource model of the action experiment
        """
        experiment = result_resource_model.experiment

        if experiment.type != ExperimentType.ACTIONS:
            raise Exception('The resource is not an action')

        # retrieve the action process, then the input action resource
        return experiment.protocol_model.get_process(
            cls.ACTION_PROCESS_INSTANCE_NAME).inputs.get_resource_model(
            ActionsTask.actions_input_name)
