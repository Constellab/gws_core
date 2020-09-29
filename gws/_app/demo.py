# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from starlette.templating import Jinja2Templates
from starlette.authentication import requires

from gws.settings import Settings

@requires("authenticated")
async def demo(request):
    settings = Settings.retrieve()
    template_dir = settings.get_template_dir("gws")
    templates = Jinja2Templates(directory=template_dir)

    return templates.TemplateResponse("demo.html", {
        "request": request, 
        "settings": settings
    })