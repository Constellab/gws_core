# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.settings import Settings
from gws.model import Resource, HTMLViewModel, JSONViewModel
from gws.view import ViewJinja2TemplateFiles

settings = Settings.retrieve()
template_dir = settings.get_template_dir("gws")

class Robot(Resource):
    pass

class HTMLRobotViewModel(HTMLViewModel):
    model_specs = [ Robot ]
    template = ViewJinja2TemplateFiles(directory=template_dir, file_path="robot/robot.html") 

class JSONRobotViewModel(JSONViewModel):
    model_specs = [ Robot ]