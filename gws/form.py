import os
from base64 import b64encode

from starlette.requests import Request
from fastapi_mail import FastMail

from gws.prism.view import HTMLViewTemplate

def crsf_protect(function):
    def wrapper(*args, **kwargs):
        for arg in args:
            if isinstance(arg, Request):
                request = arg

        if not "crsf" in request.session:
            random_bytes = os.urandom(64)
            token = b64encode(random_bytes).decode('utf-8')
            request.session["crsf"] = token
    
        return function(*args, **kwargs)

    return wrapper


def async_crsf_protect(function):
    async def wrapper(*args, **kwargs):
        for arg in args:
            if isinstance(arg, Request):
                request = arg

        if not "crsf" in request.session:
            random_bytes = os.urandom(64)
            token = b64encode(random_bytes).decode('utf-8')
            request.session["crsf"] = token

        return await function(*args, **kwargs)

    return wrapper


class FormTemplate(HTMLViewTemplate):
    def __init__(self,fields):
        self.fields = fields
    
    def render(self):
        pass
