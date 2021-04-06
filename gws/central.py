# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import requests
from gws.settings import Settings
from gws.logger import Error
from gws.report import Report
from gws.lab import Lab
from gws.model import Experiment, Protocol, User

class Central:
    
    # -- A --

    @classmethod
    def activate_user(cls, uri):
        return self.set_user_status(uri, {"is_active": True})
                
    # -- C --
    
    @classmethod
    def check_api_key(cls, api_key: str):
        settings = Settings.retrieve()
        if not settings.data.get("central"):
            return False
        return settings.data["central"].get("api_key") == api_key

    
    @classmethod
    def create_user(cls, data: dict):
        Q = User.get_by_uri(data['uri'])
        if not Q:
            user = User(
                uri = data['uri'],
                email = data['email'],
                group = data.get('group','user'),
                is_active = data.get('is_active', True),
            )
            if user.save():
                return cls.get_user_status(user.uri)
            else:
                raise Error("Central", "create_user", "Cannot save the user")
        else:
            raise Error("Central", "create_user", "The user already exists")

    # -- D --
    
    @classmethod
    def deactivate_user(cls, uri):
        return self.set_user_status(uri, {"is_active": False})
    
    # -- F --

    # -- G --

    @classmethod
    def get_user_status(cls, uri):
        user = User.get_by_uri(uri)
        if user is None:
            raise Error("Central", "get_user_status", "User not found")
        else:
            return {
                "uri": user.uri,
                "group": user.group,
                "console_token": user.console_token,
                "is_active": user.is_active,
                "is_http_authenticated": user.is_http_authenticated,
                "is_console_authenticated": user.is_console_authenticated
            }
    
    # -- L -- 
    
    # -- S --
    
    @classmethod
    def set_user_status(cls, uri, data):
        user = User.get_by_uri(uri)
        if user is None:
            raise Error("Central", "set_user_status", "User not found")
        else:
            if data.get("is_active"):
                user.is_active = data.get("is_active")
            
            if data.get("group"):
                user.group = data.get("group")
                
            if user.save():
                return cls.get_user_status(user.uri)
            else:
                raise Error("Central", "set_user_status", "Cannot save the user")
    
    # -- S --
    
    @classmethod
    def set_api_key(cls, api_key: str):
        settings = Settings.retrieve()
        if not settings.data.get("central"):
            settings.data["central"] = {}
            
        settings.data["central"]["api_key"] = api_key
        tf = settings.save()
        return { "status": tf }

    # -- V --
