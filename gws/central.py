# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import requests
from gws.settings import Settings
from gws.logger import Logger
from gws.model import Report
from gws.lab import Lab
from gws.model import Experiment, User

class Central:
    
    # -- A --

    @classmethod
    def activate_user(cls, uri):
        user = User.get_by_uri(uri)
        if user is None:
            raise Exception("User not found")
        else:
            user.is_active = True
            user.save()
            return True
            
    # -- C --

    @classmethod
    def create_user(cls, data):
        user = User.get_by_uri(data["uri"])
        if user is None:
            user = User(uri=data["uri"],token=data["token"])
            return user.save()
        else:
            raise Exception("The user already exists")
    
    @classmethod
    def close_experiment(cls, uri):
        pass

    # -- D --

    @classmethod
    def deactivate_user(cls, uri):
        user = User.get_by_uri(uri)
        if user is None:
            raise Exception("User not found")
        else:
            user.is_active = False
            user.save()
            return True

    # -- G --

    @classmethod
    def get_api_url(cls, action):
        settings = Settings.retrieve()
        url = settings.data["central"]["api_url"]
        url = url \
                .replace("{resource}", "lab") \
                .replace("{uri}", Lab.get_uri()) \
                .replace("{action}",action)

        return url

    # -- O -- 

    # @classmethod
    # def open_project(cls, data):
    #     from gws.model import Project
    #     uri = data["uri"]
    #     if Project.get_by_uri(uri) is None:
    #         p = Project(
    #             uri=uri,
    #             name=data["name"], 
    #             organization=data["organization"], 
    #         )
    #         return p.save()
    #     else:
    #         raise Exception("The project already exists")
    
    @classmethod
    def open_experiment(cls, data):
        user = User.get_by_uri(data["user_uri"])
        if user is None:
            raise Exception(f"User not found")

        exp = Experiment.get_by_uri(data["uri"])
        if exp is None:
            e = Experiment(uri = data["uri"])
            return e.save()
        else:
            return True

    # -- S --

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
    
    # -- T --

    @classmethod
    def tell_is_running(cls):
        url = cls.get_api_url("update-status")
        return cls.send(url, message={"status": "on"})
            
    @classmethod
    def tell_is_stopped(cls):
        url = cls.get_api_url("update-status")
        return cls.send(url, message={"status": "off"})