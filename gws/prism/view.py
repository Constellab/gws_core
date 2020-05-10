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

class ViewTemplate(Base):
    content: str = ''

    def __init__(self, content:str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content

    def render(self, view_model: 'ViewModel') -> str: 
        template = Template(self.content)
        context = {"view_model": view_model}
        return template.render(context)

    @staticmethod
    def from_file(file_path):
        with open(file_path, "r") as fh:
            return ViewTemplate(fh.read())   

class PlainTextViewTemplate(ViewTemplate):

    @staticmethod
    def from_file(file_path):
        with open(file_path, "r") as fh:
            return PlainTextViewTemplate(fh.read())

class JSONViewTemplate(ViewTemplate):

    @staticmethod
    def from_file(file_path):
        with open(file_path, "r") as fh:
            return JSONViewTemplate(fh.read())

class HTMLViewTemplate(ViewTemplate):

    @staticmethod
    def from_file(file_path):
        with open(file_path, "r") as fh:
            return HTMLViewTemplate(fh.read())
