# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from starlette.templating import Jinja2Templates
from gws.settings import Settings

settings = Settings.retrieve()
template_dir = settings.get_template_dir("gws")
templates = Jinja2Templates(directory=template_dir)

async def demo(request):
    return templates.TemplateResponse("demo/index.html", {
        "request": request, 
        "settings": settings
    })