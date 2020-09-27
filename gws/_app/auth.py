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

settings = Settings.retrieve()
template_dir = settings.get_template_dir("gws")
templates = Jinja2Templates(directory=template_dir)

@requires("authenticated", redirect='auth')
async def userpage(request):
    pass

@requires("authenticated")
async def authpage(request):
    if request.user.is_authenticated:
        response = RedirectResponse(url='/')
        return response
    else:
        raise AuthenticationError('Not allowed')

class AuthBackend(AuthenticationBackend):

    async def authenticate(self, request):
        #print(request.headers)
        
        #if "Authorization" not in request.headers:
        #    return
        #
        #auth = request.headers["Authorization"]
        #try:
        #    scheme, credentials = auth.split()
        #    if scheme.lower() != 'basic':
        #        return
        #    decoded = base64.b64decode(credentials).decode("ascii")
        #except (ValueError, UnicodeDecodeError, binascii.Error) as err:
        #    raise AuthenticationError(f'Invalid basic auth credentials. Error: {err}')
        #
        #email, _, password = decoded.partition(":")

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
    
# class Login(HTTPEndpoint):

#     @async_crsf_protect
#     async def get(self, request):
#         template_dir = settings.get_template_dir(settings.name)
#         templates = Jinja2Templates(directory=template_dir)
#         return templates.TemplateResponse('user/login.html', { "request": request,  "settings": settings })

#     @async_crsf_protect
#     async def post(self, request):
#         template_dir = settings.get_template_dir(settings.name)
#         templates = Jinja2Templates(directory=template_dir)

#         data = await request.form()
#         email = data.get('email')
#         password = data.get('password')
        
#         try:
#             user = User.get(email=email, password=password)
#             request.session["is_authenticated"] = True
#             return request.redirect("/")
#         except:
#             return templates.TemplateResponse('user/login.html', { "request": request, "settings": settings }) 

# class Signup(HTTPEndpoint):

#     @async_crsf_protect
#     async def get(self, request):
#         template_dir = settings.get_template_dir(settings.name)
#         templates = Jinja2Templates(directory=template_dir)
#         return templates.TemplateResponse('user/signup.html', { "request": request, "settings": settings })

#     @async_crsf_protect
#     async def post(self, request):
#         template_dir = settings.get_template_dir(settings.name)
#         templates = Jinja2Templates(directory=template_dir)

#         data = await request.form()
#         username = data.get('username')
#         email = data.get('email')
#         tasks = BackgroundTasks()
#         tasks.add_task(send_welcome_email, to_address=email)
#         tasks.add_task(send_admin_notification, username=username)

#         return templates.TemplateResponse('user/signup.html', { "request": request, "settings": settings }) 

# async def send_welcome_email(to_address):
#     subject = "Account validation"
#     message = "Your account is created"
#     await Email.send(to_address, subject, message)

# async def send_admin_notification(username):
#     pass
