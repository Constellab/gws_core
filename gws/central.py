# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import requests
from gws.settings import Settings
from gws.logger import Logger
from gws.model import Report
from gws.lab import Lab

class Central:
    
    # -- C --

    @classmethod
    def create_user(cls, uri, data):
        from gws.model import User
        if User.get_by_uri(uri) is None:
            u = User(
                uri = uri,
                firstname=data["firstname"], 
                sirname=data["sirname"], 
                organization=data["organization"], 
                email=data["email"], 
                token=data["token"]
            )
            return u.save()
        else:
            raise Exception("The user already exists")
    
    @classmethod
    def create_project(cls, uri, data):
        from gws.model import Project
        if Project.get_by_uri(uri) is None:
            p = Project(
                uri = uri,
                name=data["name"], 
                organization=data["organization"], 
            )
            return p.save()
        else:
            raise Exception("The project already exists")
    
    @classmethod
    def create_experiment(cls, uri, data):
        from gws.model import Experiment, User, Project
        if Experiment.get_by_uri(uri) is None:
            try:
                user = User.get_by_uri(data["user_uri"])
                project = Project.get_by_uri(data["project_uri"])
            except Exception as err:
                raise Exception(f"User or project not found. Error: {err}")

            e = Experiment(
                uri = uri,
                user = user,
                project = project,
            )
            return e.save()
        else:
            raise Exception("The experiment already exists")

    @classmethod
    def get_api_url(cls, action):
        settings = Settings.retrieve()
        url = settings.data["central"]["api_url"]
        url = url \
                .replace("{resource}", "lab") \
                .replace("{uri}", Lab.get_uri()) \
                .replace("{action}",action)

        return url

    @classmethod
    def send(cls, url, message={}):
        if Lab.get_uri() == "":
            return False
    
        data = {
            "lab" : Lab.get_status(),
            "message": message
        }
        try:
            response = requests.post(url, data=data)
            return response.status_code == 200
        except:
            return False

    @classmethod
    def send_status(cls, data={}):
        url = cls.get_api_url("update-status")
        cls.send(url)

    @classmethod
    def send_report(cls, report):
        url = cls.get_api_url("add-report")
        cls.send(url, message={"report_uri": report.uri})
    
    @classmethod
    def tell_is_running(cls):
        url = cls.get_api_url("update-status")
        return cls.send(url, message={"status": "on"})
            
    @classmethod
    def tell_is_stopped(cls):
        url = cls.get_api_url("update-status")
        return cls.send(url, message={"status": "off"})