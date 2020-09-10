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

from gws.form import async_crsf_protect
from gws.mail import Email
from gws.settings import Settings

settings = Settings.retrieve()
template_dir = settings.get_template_dir("gws")
templates = Jinja2Templates(directory=template_dir)

@async_crsf_protect
async def login(request):
    template_dir = settings.get_template_dir(settings.name)
    templates = Jinja2Templates(directory=template_dir)
    return templates.TemplateResponse('user/login.html', {
        "request": request, 
        "settings": settings
    })

@requires("authenticated", redirect='login')
async def user(request):
    pass

class Signup(HTTPEndpoint):

    @async_crsf_protect
    async def get(self, request):
        template_dir = settings.get_template_dir(settings.name)
        templates = Jinja2Templates(directory=template_dir)
        return templates.TemplateResponse('user/singup.html', {
            "request": request, 
            "settings": settings
        })

    #@async_crsf_potect
    async def post(self, request):
        template_dir = settings.get_template_dir(settings.name)
        templates = Jinja2Templates(directory=template_dir)

        data = await request.json()
        username = data['username']
        email = data['email']
        tasks = BackgroundTasks()
        tasks.add_task(send_welcome_email, to_address=email)
        tasks.add_task(send_admin_notification, username=username)

        return templates.TemplateResponse('user/singup.html', {
            "request": request, 
            "settings": settings
        }) 

async def send_welcome_email(to_address):
    subject = "Account validation"
    message = "Your account is created"
    await Email.send(to_address, subject, message)

async def send_admin_notification(username):
    pass
