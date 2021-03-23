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

class Central:
    
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CANNOT_SAVE = "CANNOT_SAVE"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    
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
                is_locked = data.get('is_locked', False)
            )
            if user.save():
                return cls.get_user_status(user.uri)
            else:
                return {"exception": {"id": cls.CANNOT_SAVE, "message": f"Cannot save the user"}}
        else:
            return {"exception": {"id": cls.ALREADY_EXISTS, "message": f"The user already exists"}}

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
            return {"exception": {"id": cls.NOT_FOUND, "message": f"User not found"}}
        else:
            return {
                "uri": user.uri,
                "group": user.group,
                "is_active": user.is_active,
                "is_locked": user.is_locked
            }
    
    # -- L -- 
    
    @classmethod
    def lock_user(cls, uri):
        return self.set_user_status(uri, {"is_locked": True})
    
    # -- S --
    
    @classmethod
    def set_user_status(cls, uri, data):
        user = User.get_by_uri(uri)
        if user is None:
            return {"exception": {"id": cls.NOT_FOUND, "message": f"User not found"}}
        else:
            if data.get("is_locked"):
                user.is_locked = data.get("is_locked")
            
            if data.get("is_active"):
                user.is_active = data.get("is_active")
            
            if data.get("group"):
                user.group = data.get("group")
                
            if user.save():
                return cls.get_user_status(user.uri)
            else:
                return {"exception": {"id": cls.CANNOT_SAVE, "message": f"Cannot save the user"}}
    
    # -- U --
    
    @classmethod
    def unlock_user(cls, uri):
        return self.set_user_status(uri, {"is_locked": False})
    
    # -- V --

    @classmethod
    def verify_api_key(cls, central_api_key: str):
        settings = Settings.retrieve()
        return settings.get_data("central_api_key") == central_api_key
