# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import requests
from gws.settings import Settings
from gws.logger import Logger
from gws.report import Report
from gws.lab import Lab
from gws.model import Experiment, User, Protocol

class Central:
    
    api = {
        "put-status"    : "/external-labs/lab-instance/status/{status}",
        "post-report"   : "/external-labs/{experiment_id}/report"
    }

    # -- A --

    @classmethod
    def activate_user(cls, uri):
        user = User.get_by_uri(uri)
        if user is None:
            Logger.error(Exception("Central", "activate_user", "User not found"))
        else:
            user.is_active = True
            user.save()
            return True
            
    # -- C --

    @classmethod
    def create_user(cls, data: dict):
        user = User.get_by_uri(data['uri'])
        if user is None:
            user = User(uri=data['uri'])
            if user.save():
                return {
                    "uri": user.uri,
                }
            else:
                Logger.error(Exception("Central", "create_user", "Cannot save the user"))
        else:
            Logger.error(Exception("Central", "create_user", "The user already exists"))
    
    @classmethod
    def create_experiment(cls, data):
        if data.get("uri", None):
            e = Experiment.get_by_uri(data["uri"])
        else:
            e = None
            
        if not e:
            if 'protocol' in data:
                
                if not data["protocol"].get("uri", None):
                    Logger.error(Exception("Central", "create_experiment", f"No protocol uri found"))
                    
                proto = Protocol.get_by_uri(data["protocol"]["uri"])
                if proto is None:
                    graph = data["protocol"].get("graph", None)
                    if graph is None:
                        Logger.error(Exception("Central", "create_experiment", f"No protocol graph found"))
                    else:
                        try:
                            proto = Protocol.from_graph(graph)
                            proto.save()
                        except Exception as err:
                            Logger.error(Exception("Central", "create_experiment", f"Protocol graph is not valid. Error: {err}"))

            else:
                Logger.error(Exception("Central", "create_experiment", f"Protocol not defined"))
                
            e = proto.create_experiment()
            e.uri = data["uri"]
            if e.save():
                return e
            else:
                Logger.error(Exception("Central", "create_experiment", f"Cannot save the experiment"))
        else:
            Logger.error(Exception("Central", "create_experiment", f"The experiment already exists"))

    @classmethod
    def create_url(cls, action, **kwargs):
        settings = Settings.retrieve()
        url = settings.data["central"]["api_url"] + cls.api[action]

        for k in kwargs:
            url = url.replace("{"+k+"}", kwargs[k])

        return url

    @classmethod
    def close_experiment(cls, uri):
        exp = Experiment.get_by_uri(uri)
        if exp is None:
            Logger.error(Exception("Central", "close_experiment", "Experiment not found"))
        else:
            exp.is_in_process = False
            return exp.save()

    @classmethod
    def delete_experiment(cls, uri):
        exp = Experiment.get_by_uri(uri)
        if exp is None:
            Logger.error(Exception("Central", "delete_experiment", "Experiment not found"))
        else:
            exp.delete = True
            return exp.save()

    # -- D --

    @classmethod
    def deactivate_user(cls, uri):
        user = User.get_by_uri(uri)
        if user is None:
            Logger.error(Exception("Central", "deactivate_user", "User not found"))
        else:
            user.is_active = False
            return user.save()

    # -- G --

    @classmethod
    def get_user_status(cls, uri):
        user = User.get_by_uri(uri)
        if user is None:
            Logger.error(Exception("Central", "get_user_status", "User not found"))
        else:
            return {
                "uri": user.uri,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "is_locked": user.is_locked
            }

    @classmethod
    def get_protocol(csl, uri):
        proto = Protocol.get_by_uri(uri)
        if proto is None:
            Logger.error(Exception("Central", "get_protocol", "Protocol not found"))
        else:
            return {
                "uri": proto.uri,
                "graph": proto.dumps(as_dict = True)
            }
    

    # -- S --

    @classmethod
    def send(cls, url, method='GET', data={}):
        is_online = Lab.get_uri() == ""
        if not is_online:
            return False

        header = {"GWS-Lab-Token": Lab.get_token()}
        try:
            if method.upper() == "POST":
                response = requests.post(url, data=data, headers=header)
            elif method.upper() == "PUT":
                response = requests.put(url, data=data, headers=header)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=header)
            else:
                response = requests.get(url, headers=header)

            return response.status_code == 200
        except:
            return False

    @classmethod
    def put_status(cls, is_running: bool = True):
        if is_running:
            status = "running"
        else:
            status = "stopped"

        url = cls.create_url("put-status", status=status)
        cls.send(url, method="PUT")

    @classmethod
    def post_report(cls, report):
        url = cls.create_url("post-report", experiment_id=report.experiment.id)
        cls.send(url, method="POST", data={"report_uri": report.uri})
    
    # -- V --

    @classmethod
    def verify_api_key(cls, central_api_key: str):
        settings = Settings.retrieve()
        return settings.get_data("central_api_key") == central_api_key
