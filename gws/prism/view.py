#
# Python GWS view
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#

import asyncio
import json
from starlette.responses import Response, HTMLResponse, JSONResponse, PlainTextResponse
from jinja2 import Template

from gws.prism.base import Base
from gws.prism.model import ViewModel, Model
from gws.prism.controller import Controller

class View(Base):
    name: str = None        #@replace name => target
    content : str = ''

    #_type: str = 'view'
    _model: 'Model'
    _view_model: 'ViewModel'
    

    def __init__(self, model: 'Model', content: str = None):
        if not content is None:
            if not isinstance(content, str):
                raise Exception(self.classname(), "__init__", "The content must be a string")
            self.content = content
        
        if self.name is None:
            raise Exception(self.classname(), "__init__", "No view name povided. It seems that you did set this property in the definition of the class")
        
        if model is None:
            raise Exception(self.classname(),"__init__","A model is required")

        self._model = model
        self._view_model = ViewModel(self)
        
        #uuid = view.view_model.uuid
        #self._view_instances[uuid] = view
        #self._view_types[view.name] = type(view)
            
        Controller.register(self)

    @staticmethod
    def from_file(file_path):
        with open(file_path, "r") as fh:
            return View(fh.read())   

    @property
    def model(self):
        return self._model

    def render(self, params: dict) -> str:
        template = Template(self.content)
        context = {"params": params, "view": self}
        self.set_params(params)
        return template.render(context)
    
    @property
    def params(self) -> dict:
        return self._view_model.params

    def set_params(self, params: dict):
        self._view_model.set_params(params)

    # def set_model(self, model: 'Model'):
    #     from gws.prism.model import Model
    #     if not isinstance(model, Model):
    #         raise Exception(self.classname(), "set_model", "The model must be an instance of Model")

    #     self._model = model

    @property
    def uri(self):
        return self._view_model.uri

    @property
    def view_model(self):
        return self._view_model

class PlainTextView(View):

    @staticmethod
    def from_file(file_path):
        with open(file_path, "r") as fh:
            return PlainTextView(fh.read())

class JSONView(View):

    @staticmethod
    def from_file(file_path):
        with open(file_path, "r") as fh:
            return JSONView(fh.read())

class HTMLView(View):

    @staticmethod
    def from_file(file_path):
        with open(file_path, "r") as fh:
            return HTMLView(fh.read())
