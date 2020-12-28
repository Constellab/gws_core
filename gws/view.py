# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import json
import os

from fastapi.templating import Jinja2Templates
from jinja2 import Template

from gws.base import Base
from gws.logger import Error
from gws.settings import Settings

class ViewTemplate(Base):
    """
    ViewTemplate class.
    This file allows rendering Jinja2 template contents. 

    To learn more about Jinja2, please see https://jinja.palletsprojects.com/.

    :property content: The Jinja2 template content
    :type content: str
    :property type: Type of the view template rendering
    * 'text/plain' for plain text rendering
    * 'text/html' for HTML text rendering
    * 'application/json' for JSON text rendering
    :type content: str
    """

    content: str = ''
    type: str = 'text/plain'
  
    def __init__(self, content:str = '', type = 'text/plain', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content
        self.type = type


    def is_html(self) -> bool:
        """
        Returns True if the rendering of the view template is a HTML text, False otherwise
        """
        return self.type == 'text/html'

    def is_plain_text(self) -> bool:
        """
        Returns True if the rendering of the view template is a plain text, False otherwise
        """
        return self.type == 'text/plain'

    def is_json(self) -> bool:
        """
        Returns True if the rendering of the view template is a JSON text, False otherwise
        """
        return self.type == 'application/json'

    def render(self, vmodel: 'ViewModel' = None) -> str: 
        """
        Returns the rendering of the view template.

        :param vmodel: The view model to render
        :type vmodel: ViewModel
        :return: The rendering string
        :rtype: str
        """
        template = Template(self.content)
        return template.render({
            "vmodel": vmodel,
            "vdata": vmodel.data,
            "mdata": vmodel.model.data,
            "settings": Settings.retrieve(),
        })

    @staticmethod
    def from_file(file_path) -> 'ViewTemplate':
        """
        Constructs a ViewTemplate instance and loads its content from a file

        :param file_path: The file path
        :type file_path: str
        :return: The view template
        :rtype: ViewTemplate
        """

        with open(file_path, "r") as fh:
            return ViewTemplate(fh.read())   

class PlainTextViewTemplate(ViewTemplate):
    """
    PlainTextViewTemplate class.
    This file allows rendering Jinja2 template contents. The rendering is a plain text.

    To learn more about Jinja2, please see https://jinja.palletsprojects.com/.
    """

    def __init__(self, content, type='text/plain', *args, **kwargs):
        super().__init__(content, type=type, *args, **kwargs)

    @staticmethod
    def from_file(file_path):
        """
        Constructs a PlainTextViewTemplate instance and loads its content from a file

        :param file_path: The file path
        :type file_path: str
        :return: The view template
        :rtype: PlainTextViewTemplate
        """

        with open(file_path, "r") as fh:
            return PlainTextViewTemplate(fh.read())

class JSONViewTemplate(ViewTemplate):
    """
    JSONViewTemplate class.
    This file allows rendering Jinja2 template contents. The rendering is a JSON text.

    To learn more about Jinja2, please see https://jinja.palletsprojects.com/.
    """

    def __init__(self, content, type='application/json', *args, **kwargs):
        super().__init__(content, type=type, *args, **kwargs)

    @staticmethod
    def from_file(file_path):
        """
        Constructs a JSONViewTemplate instance and loads its content from a file

        :param file_path: The file path
        :type file_path: str
        :return: The view template
        :rtype: JSONViewTemplate
        """

        with open(file_path, "r") as fh:
            return JSONViewTemplate(fh.read())

class HTMLViewTemplate(ViewTemplate):
    """
    HTMLViewTemplate class.
    This file allows rendering Jinja2 template contents. The rendering is a HTML text.

    To learn more about Jinja2, please see https://jinja.palletsprojects.com/.
    """

    def __init__(self, content, type='text/html', *args, **kwargs):
        super().__init__(content, type=type, *args, **kwargs)

    @staticmethod
    def from_file(file_path):
        """
        Constructs a HTMLViewTemplate instance and loads its content from a file

        :param file_path: The file path
        :type file_path: str
        :return: The view template
        :rtype: HTMLViewTemplate
        """

        with open(file_path, "r") as fh:
            return HTMLViewTemplate(fh.read())

class ViewTemplateFile(ViewTemplate):
    """
    ViewTemplateFile class.
    This file allows rendering Jinja2 template files. The rendering is a can be a Plain, HTML or JSON text.

    To learn more about Jinja2, please see https://jinja.palletsprojects.com/.
    """

    def __init__(self, file_path, type='text/plain', *args, **kwargs):
        
        content = ""
        if file_path == "":
            raise Error("ViewTemplateFile", "__init__", "A valid file path is required")
        else:
            if os.path.exists(file_path):
                fl = open(file_path, "r")
                content = fl.read()
                fl.close()
            else:
                raise Error("ViewTemplateFile", "__init__", "The template file is not found")

        super().__init__(content, type=type, *args, **kwargs)


class ViewJinja2TemplateFiles(ViewTemplate):
    """
    ViewJinja2TemplateFiles class.
    This file allows rendering Jinja2 template files using a directory of templates.

    To learn more about Jinja2, please see https://jinja.palletsprojects.com/.

    :property directory: The Jinja2 directory of templates
    :type directory: str
    :property file_path: The path of the entry file (in the :property:`directory`) to render
    :type file_path: str
    """

    directory = None
    file_path = None

    def __init__(self, directory: str, file_path: str, *args, **kwargs):
        super().__init__(content='', type='text/html', *args, **kwargs)

        self.directory = directory
        self.file_path = file_path

    def render(self, vmodel: 'ViewModel' = None) -> str: 
        """
        Returns the rendering of the view template.

        :param vmodel: The view model to render
        :type vmodel: ViewModel
        :return: The response
        :rtype: str
        """

        templates = Jinja2Templates(directory=self.directory)

        return templates.TemplateResponse(self.file_path, {
            "vmodel": vmodel,
            "mdata" : vmodel.data,
            "vdata" : vmodel.model.data,
            "settings": Settings.retrieve()
        })