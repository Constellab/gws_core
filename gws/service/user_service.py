# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from starlette_context import context

from gws.query import Paginator
from gws.logger import Error
from gws.model import Activity, User
from gws.http import *

from .base_service import BaseService

class UserService(BaseService):
    
    _console_data = { "user": None }
    
    # -- A --
    
    @classmethod
    def activate_user(cls, uri) -> User:
        return cls.set_user_status(uri, {"is_active": True})

    
    # -- C --
    
    @classmethod
    def create_user(cls, data: dict) -> User:
        group = data.get('group', 'user')
        if group == "sysuser":
            raise Error("Central", "create_user", "Cannot create sysuser")

        u = User.get_by_uri(data['uri'])
        if not u:
            user = User(
                uri=data['uri'],
                email=data['email'],
                group=group,
                is_active=data.get('is_active', True),
                data={
                    "first_name": data['first_name'],
                    "last_name": data['last_name'],
                }
            )
            if user.save():
                return User.get_by_uri(user.uri)
            else:
                raise Error("Central", "create_user",
                            "Cannot create the user")
        else:
            raise Error("Central", "create_user",
                        "The user already exists")
    
    # -- D --
    
    @classmethod
    def deactivate_user(cls, uri) -> User:
        return cls.set_user_status(uri, {"is_active": False})

    # -- F --
    
    @classmethod
    def fecth_activity_list(cls, \
                            user_uri: str=None, \
                            activity_type: str=None, \
                            page:int=1, \
                            number_of_items_per_page:int=20, \
                            as_json = False ) -> (Paginator, dict, ):
        
        Q = Activity.select()\
                    .order_by(Activity.creation_datetime.desc())
        
        if user_uri:
            Q = Q.join(User).where(User.uri == user_uri)
            
        if activity_type:
            Q = Q.where(Activity.activity_type == activity_type.upper())
        
        P = Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return P.to_json()
        else:
            return P
    
    @classmethod
    def fetch_user(cls, uri: str) -> User:
        return User.get_by_uri(uri)
    
    @classmethod
    def fetch_user_list(cls, \
                        page:int=1, \
                        number_of_items_per_page: int=20, \
                       as_json = False) -> (Paginator, dict, ):
        
        Q = User.select()\
                .order_by(User.creation_datetime.desc())
        
        P = Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page)
        
        if as_json:
            return P.to_json()
        else:
            return P
    
    # -- G --
    
    @classmethod
    def get_current_user(cls) -> User:
        """
        Get the user in the current session
        """
        
        try:
            user = context.data["user"]
        except:
            # is console context
            try:
                user = cls._console_data["user"]
            except:
                raise Error("Controller", "get_current_user", "No HTTP nor Console user authenticated")
        
        if user is None:
            raise Error("Controller", "get_current_user", "No HTTP nor Console user authenticated")
        
        return user

    @classmethod
    def get_user_by_uri(cls, uri: str) -> User:
        return User.get_by_uri(uri)
    
    # -- S --
    
    @classmethod
    def set_user_status(cls, uri, data) -> User:
        user = User.get_by_uri(uri)
        if user is None:
            raise Error("Central", "set_user_status", "User not found")
        else:
            if not data.get("is_active") is None:
                user.is_active = data.get("is_active")

            if data.get("group"):
                user.group = data.get("group")

            if user.save():
                return user
            else:
                raise Error("Central", "set_user_status",
                            "Cannot save the user")
    
    @classmethod
    def set_current_user(cls, user: (User, )):
        """
        Set the user in the current session
        """
        
        if user is None:
            try:
                # is http context
                context.data["user"] = None
            except:
                # is console context
                cls._console_data["user"] = None
        else:  
            if isinstance(user, dict):
                try:
                    user = User.get(User.uri==user.uri)
                except:
                    raise HTTPInternalServerError(detail=f"Invalid current user")

            if not isinstance(user, User):
                raise HTTPInternalServerError(detail=f"Invalid current user")

            if not user.is_active:
                raise HTTPUnauthorized(detail=f"Not authorized")

            try:
                # is http contexts
                context.data["user"] = user
            except:
                # is console context
                cls._console_data["user"] = user

    @classmethod
    def get_all_users(cls):
        return list(User.select())
    
