

from typing import List

from fastapi import Depends

from gws_core.core.utils.logger import Logger
from gws_core.process.process_dto import ProcessDTO
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.task.task_input_model import TaskInputModel

from ..core_controller import core_app
from ..user.auth_service import AuthService
from .task_service import TaskService


@core_app.get("/task/{id}", tags=["Task"], summary="Get a task")
def get_a_task(id: str,
               _=Depends(AuthService.check_user_access_token)) -> ProcessDTO:
    """
    Retrieve a task

    - **type**: the type of the task (Default is `gws_core.task.task_model.Task`)
    - **id**: the id of the task
    """

    return TaskService.get_task_by_id(id=id).to_dto()


# TODO CHECK WHAT TO DO WITH THIS
@core_app.post("/task/{id}/fix", tags=["Task"], summary="Fix a task")
def fix_a_task(id: str,
               _=Depends(AuthService.check_user_access_token)) -> None:
    """
    Fix a task

    - **type**: the type of the task (Default is `gws_core.task.task_model.Task`)
    - **id**: the id of the task
    """

    protocol: ProtocolModel = ProtocolModel.get_by_id_and_check(id)
    fix_protocol(protocol)


@core_app.post("/task/fix", tags=["Task"], summary="Run a task")
def fix_all_protocol(_=Depends(AuthService.check_user_access_token)):
    Logger.info('Start fixing all protocols')
    protocol_models = list(ProtocolModel.select())
    for protocol in protocol_models:
        try:
            fix_protocol(protocol)
        except Exception as e:
            Logger.error(f"Error while fixing protocol {protocol.id} : {e}")
            Logger.log_exception_stack_trace(e)
            continue
    Logger.info('End fixing all protocols')


def fix_protocol(protocol: ProtocolModel):
    for process in protocol.processes.values():
        task_input_model: List[TaskInputModel] = list(
            TaskInputModel.get_by_task_model(process.id))

        for task_input in task_input_model:

            if not process.inputs.port_exists(task_input.port_name):
                Logger.error(
                    f"Port {task_input.port_name} does not exist in {process.id}, in protocol {protocol.id}")
                continue

            port = process.in_port(task_input.port_name)
            if port is None:
                Logger.error(
                    f"Port {task_input.port_name} not found in process {process.id}, in protocol {protocol.id}")
                continue

            # set the input of the process
            port.set_resource_model(task_input.resource_model)
            process.data["inputs"] = process.inputs.to_json()

            # set the output of the previous process
            connector = protocol.get_connector_from_right(
                process.instance_name, task_input.port_name)

            if connector is None:
                Logger.error(
                    f"No connector found for {process.instance_name}:{task_input.port_name}, in protocol {protocol.id}")
                continue

            connector.left_port.set_resource_model(task_input.resource_model)
            connector.left_process.data["outputs"] = connector.left_process.outputs.to_json(
            )

    protocol.save_full()
