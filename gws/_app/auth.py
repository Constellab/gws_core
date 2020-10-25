# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from starlette.endpoints import HTTPEndpoint
from starlette.templating import Jinja2Templates
from starlette.authentication import requires
from starlette.responses import HTMLResponse
from starlette.background import BackgroundTasks
from fastapi_mail import FastMail
from starlette.authentication import (
    AuthenticationBackend, AuthenticationError, SimpleUser, UnauthenticatedUser,
    AuthCredentials
)
from starlette.responses import RedirectResponse


from gws.form import async_crsf_protect
from gws.mail import Email
from gws.settings import Settings
from gws.session import Session

def get_templates():
    settings = Settings.retrieve()
    template_dir = settings.get_template_dir("gws")
    return Jinja2Templates(directory=template_dir), settings

@requires("authenticated")
async def login_page(request):
    if request.user.is_authenticated:
        response = RedirectResponse(url='/')
        return response
    else:
        raise AuthenticationError('Not allowed')

@requires("authenticated")
async def logout_page(request):
    templates, settings = get_templates()
    if request.user.is_authenticated:
        request.session['token'] = None
    
    return templates.TemplateResponse("auth/logout.html", {
        'request': request, 
        'settings': settings,
    })

class AuthBackend(AuthenticationBackend):

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
