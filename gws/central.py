# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import requests
from gws.settings import Settings
from gws.logger import Error
from gws.report import Report
from gws.lab import Lab
from gws.model import Experiment, Protocol
from gws.user import User
from gws.http import *

class Central:
    
    # -- A --

    @classmethod
    def activate_user(cls, uri):
        return self.set_user_status(uri, {"is_active": True})
                
    # -- C --

    @classmethod
    def create_user(cls, data: dict):
        Q = User.get_by_uri(data['uri'])
        if not Q:
            user = User(
                uri = data['uri'],
                token = data['token'],
                email = data['email'],
                group = data.get('group','user'),
                is_active = data.get('is_active', True),
            )
            if user.save():
                return cls.get_user_status(user.uri)
            else:
                raise HTTPInternalServerError(detail=f"Cannot save the user")
        else:
            raise HTTPInternalServerError(detail=f"The user already exists")

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
            raise HTTPNotFound(detail=f"User not found")
        else:
            return {
                "uri": user.uri,
                "token": user.token,
                "group": user.group,
                "is_active": user.is_active,
            }
    
    # -- L -- 
    
    # -- S --
    
    @classmethod
    def set_user_status(cls, uri, data):
        user = User.get_by_uri(uri)
        if user is None:
            raise HTTPNotFound(detail=f"User not found")
        else:
            if data.get("is_active"):
                user.is_active = data.get("is_active")
            
            if data.get("group"):
                user.group = data.get("group")
                
            if user.save():
                return cls.get_user_status(user.uri)
            else:
                raise HTTPInternalServerError(detail=f"Cannot save the user")
    
    # -- U --
    
    # -- V --

    @classmethod
    def verify_api_key(cls, central_api_key: str):
        settings = Settings.retrieve()
        return settings.get_data("central_api_key") == central_api_key
