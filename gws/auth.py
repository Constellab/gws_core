# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends, FastAPI

from gws.form import async_crsf_protect
from gws.mail import Email
from gws.settings import Settings
from gws.session import Session



async def authenticate(self, request):
    settings = Settings.retrieve()
    if not settings.get_data("is_demo"):
        token = request.query_params.get("token", None)
        
        if token is None:
            token = request.session.get("token", None)

        if token == settings.get_data("token"):
            request.session['token'] = token
        else:
            raise AuthenticationError('Authentication failed')

    try:
        user = Session.get_user() #User.get(email=email, password=password)
    except:
        raise AuthenticationError('User not found')
    
    user.is_authenticated = True
    scopes = ["authenticated"]
    if user.is_admin:
        scopes.append("admin")

    auth_credentials = AuthCredentials(scopes)
    return auth_credentials, user