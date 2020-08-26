# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import json
import os
from starlette.responses import Response, HTMLResponse, JSONResponse, PlainTextResponse
from jinja2 import Template

from gws.prism.base import Base
from gws.logger import Logger

class ViewTemplate(Base):
    content: str = ''
    type: str = 'plain/text'
  
    def __init__(self, content:str, type = 'plain/text', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content
        self.type = type


    def is_html(self):
        return self.type == 'html'

    def is_plain_text(self):
        return self.type == 'plain/text'

    def is_json(self):
        return self.type == 'json'

    def render(self, view_model: 'ViewModel') -> str: 
        template = Template(self.content)
        context = {"view_model": view_model}
        return template.render(context)

    @staticmethod
    def from_file(file_path):
        with open(file_path, "r") as fh:
            return ViewTemplate(fh.read())   

class PlainTextViewTemplate(ViewTemplate):

    def __init__(self, content, type='plain/text', *args, **kwargs):
        super().__init__(content, type=type, *args, **kwargs)

    @staticmethod
    def from_file(file_path):
        with open(file_path, "r") as fh:
            return PlainTextViewTemplate(fh.read())

class JSONViewTemplate(ViewTemplate):
    def __init__(self, content, type='json', *args, **kwargs):
        super().__init__(content, type=type, *args, **kwargs)

    @staticmethod
    def from_file(file_path):
        with open(file_path, "r") as fh:
            return JSONViewTemplate(fh.read())

class HTMLViewTemplate(ViewTemplate):
    def __init__(self, content, type='html', *args, **kwargs):
        super().__init__(content, type=type, *args, **kwargs)

    @staticmethod
    def from_file(file_path):
        with open(file_path, "r") as fh:
            return HTMLViewTemplate(fh.read())

class ViewTemplateFile(ViewTemplate):
    def __init__(self, file_path, type='plain/text', *args, **kwargs):

        content = ""
        if file_path == "":
            Logger.error(Exception("ViewTemplateFile", "__init__", "A valid file path is required"))
        else:
            if os.path.exists(file_path):
                fl = open(file_path, "r")
                content = fl.read()
                fl.close()
            else:
                Logger.error(Exception("ViewTemplateFile", "__init__", "The template file is not found"))

        super().__init__(content, type=type, *args, **kwargs)

       

        