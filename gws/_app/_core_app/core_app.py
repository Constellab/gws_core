# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette_context.middleware import ContextMiddleware
from pydantic import BaseModel

from ...http import *

core_app = FastAPI(docs_url="/docs")

# Enable core for the API
core_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

core_app.add_middleware(
    ContextMiddleware
)

class ProcessData(BaseModel):
    uri:str
    type:str = "gws.process.Process"
    title:str = None
    instance_name: str
    config_specs: dict = {}
    input_specs: dict = {}
    output_specs: dict = {}

class ConfigData(BaseModel):
    uri:str = None
    type:str = "gws.config.Config"
    params: dict = {}
    
class ProtocolData(ProcessData):
    type: str = "gws.protocol.Protocol"
    interfaces: dict = {}
    outerfaces: dict = {}
