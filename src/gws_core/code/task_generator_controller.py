

from fastapi import Depends
from fastapi.responses import StreamingResponse

from gws_core.code.agent_factory import AgentFactory
from gws_core.community.community_dto import CommunityAgentFileDTO
from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.core_controller import core_app
from gws_core.user.auth_service import AuthService


@core_app.post("/task-generator/from-agent/{id}", tags=["Task generator"],
               summary="generate task code from agent")
def generate_task_code_from_agent(id: str,
                                  _=Depends(AuthService.check_user_access_token)) -> StreamingResponse:
    code = AgentFactory.generate_task_code_from_agent_id(id)

    # create a file response
    return ResponseHelper.create_file_response_from_str(code, 'task_code.py')


@core_app.post("/task-generator/agent-file/{id}", tags=["Task generator"],
               summary="generate agent task file from agent")
def generate_agent_file_from_agent(id: str,
                                   _=Depends(AuthService.check_user_access_token)) -> StreamingResponse:
    code: CommunityAgentFileDTO = AgentFactory.generate_agent_file_from_agent_id(id)

    # create a file response
    return ResponseHelper.create_file_response_from_object(code, 'agent_file.json')
