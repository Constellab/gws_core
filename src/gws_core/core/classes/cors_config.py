# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, Literal

from fastapi.applications import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..utils.settings import Settings


class CorsConfig():

    _ALLOW_ANY_ORIGIN = '*'
    _ALLOW_CREDENTIALS = True
    _ALLOW_METHODS = ["*"]
    _ALLOW_HEADERS = ["*"]

    _app: FastAPI

    @classmethod
    def configure_app_cors(cls, app: FastAPI) -> Any:
        # save the app to be able to retrieve the cors latter
        cls._app = app

        # Enable core for the API
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=cls._get_allow_origin_regex(),
            allow_credentials=cls._ALLOW_CREDENTIALS,
            allow_methods=cls._ALLOW_METHODS,
            allow_headers=cls._ALLOW_HEADERS,
        )

    @classmethod
    def configure_response_cors(cls, request: Request, response: Response) -> Response:
        """Manually configure the response with cors information, this use the actual cors config

        """

        origin = request.headers.get('origin')

        if origin:
            # Have the middleware do the heavy lifting for us to parse
            # all the config, then update our response headers
            cors = CorsConfig._get_cors()

            # Logic directly from Starlette's CORSMiddleware:
            # https://github.com/encode/starlette/blob/master/starlette/middleware/cors.py#L152

            response.headers.update(cors.simple_headers)
            has_cookie = "cookie" in request.headers

            # If request includes any cookie headers, then we must respond
            # with the specific origin instead of '*'.
            if cors.allow_all_origins and has_cookie:
                response.headers["Access-Control-Allow-Origin"] = origin

            # If we only allow specific origins, then we have to mirror back
            # the Origin header in the response.
            elif not cors.allow_all_origins and cors.is_allowed_origin(origin=origin):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers.add_vary_header("Origin")

        return response

    @classmethod
    def _get_cors(cls) -> CORSMiddleware:
        return CORSMiddleware(
            app=cls._app,
            allow_origin_regex=cls._get_allow_origin_regex(),
            allow_credentials=cls._ALLOW_CREDENTIALS,
            allow_methods=cls._ALLOW_METHODS,
            allow_headers=cls._ALLOW_HEADERS,

        )

    @classmethod
    def _get_allow_origin_regex(cls) -> str:
        # in local enviornment we allow all origins
        lab_env: Literal["PROD", "LOCAL"] = Settings.get_lab_environment()

        if lab_env == "LOCAL":
            return "." + cls._ALLOW_ANY_ORIGIN

        # In prod env we allow origin only from the virtual host (like tokyo.gencovery.io)
        virtual_host: str = Settings.get_virtual_host()

        if virtual_host is None:
            raise Exception(
                "Can't configure the lab, the environment variable 'VIRTUAL_HOST' is missing")

        # allow all request from sub domain or virtual host
        return "https://.*\." + virtual_host.replace('.', '\.')  # escape the . in virtual host
