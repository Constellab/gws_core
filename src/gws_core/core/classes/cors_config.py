from dataclasses import dataclass, field
from typing import Any

from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from gws_core.lab.lab_model.lab_enums import LabEnvironment

from ..utils.settings import Settings


@dataclass(frozen=True)
class CorsPolicy:
    """A CORS policy a registered sub-app applies to *all* of its own routes.

    Passed to ``ApiRegistry.register_api(cors=...)`` to replace the lab-wide policy
    for that app. Omit it and the app keeps the lab default: only the lab's own
    sub-domains, with credentials — which is what an internal API wants.

    A policy is deliberately per-app, not per-route: listing routes at registration
    duplicated what the route decorators already say, and drifted from them. The
    trade-off is that a policy opens *every* route on the app that its ``methods``
    allow. Hence the two guard rails below.

    :param origins: exact origins allowed, or ``["*"]`` for any. Beware: a list
        containing ``"*"`` is treated by Starlette as fully open.
    :param methods: methods the policy grants. Kept to ``GET`` by default: a
        cross-origin write should be a deliberate act, not a side effect of opening
        a read endpoint.
    :param allow_credentials: honour cookies cross-origin. Defaults to False and
        should stay there for any app opened to third-party origins — combined with
        a permissive ``origins`` it would let those sites read cookie-authenticated
        responses. The CORS spec also forbids pairing it with ``origins=["*"]``.
    :param headers: request headers the policy allows (``["*"]`` by default).

    Security note: because the policy covers the whole app, every route on it that
    matches ``methods`` becomes readable from ``origins``. Do not mount a
    cookie-authenticated route on an app whose policy is open to third parties.
    """

    origins: list[str]
    methods: list[str] = field(default_factory=lambda: ["GET"])
    allow_credentials: bool = False
    headers: list[str] = field(default_factory=lambda: ["*"])

    def __post_init__(self) -> None:
        if self.allow_credentials and "*" in self.origins:
            raise ValueError(
                "CorsPolicy(allow_credentials=True) cannot be combined with "
                "origins=['*']: browsers reject that pairing (CORS spec). List the "
                "exact origins instead."
            )

    def middleware_kwargs(self) -> dict[str, Any]:
        """This policy as ``CORSMiddleware`` keyword arguments."""
        return {
            "allow_origins": self.origins,
            "allow_credentials": self.allow_credentials,
            "allow_methods": self.methods,
            "allow_headers": self.headers,
        }

    def build_middleware(self, app: ASGIApp) -> CORSMiddleware:
        """Wrap ``app`` in a Starlette CORSMiddleware enforcing this policy."""
        return CORSMiddleware(app=app, **self.middleware_kwargs())


class LabDefaultCorsMiddleware(CORSMiddleware):
    """CORSMiddleware enforcing the lab default policy: the lab's own sub-domains
    only, with credentials.

    Added by ``ApiRegistry.register_api`` on every sub-app that declares no
    :class:`CorsPolicy` of its own. It exists because the default policy depends on
    ``Settings`` (lab environment, virtual host), which is not guaranteed to be
    loaded at brick import time, when ``register_api`` runs. ``add_middleware``
    only records the class; construction — and thus the ``Settings`` read — happens
    when the app builds its middleware stack, on its first request.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app, **CorsConfig.lab_cors_kwargs())


async def _unreachable_asgi_app(scope: Scope, receive: Receive, send: Send) -> None:
    """Placeholder for CORSMiddleware instances used only for header computation."""
    raise RuntimeError("This ASGI app is a placeholder and must never be called")


class CorsConfig:
    _ALLOW_ANY_ORIGIN = "*"
    _ALLOW_CREDENTIALS = True
    _ALLOW_METHODS = ["*"]
    _ALLOW_HEADERS = ["*"]

    @classmethod
    def configure_response_cors(
        cls, request: Request, response: Response, policy: CorsPolicy | None = None
    ) -> Response:
        """Manually configure the response with cors information.

        Needed for responses built outside the CORS middleware: a 500 handler
        response is produced by its app's ServerErrorMiddleware, ABOVE the app's
        CORS middleware, so it never traverses it.

        :param policy: the CORS policy of the app owning the request, so the
            stamped headers match what its middleware would have applied. None
            means the lab default policy.

        Note: security headers need the same treatment — the caller stamps them
        (see ``ApiRegistry.configure_exception_handlers``)
        """

        origin = request.headers.get("origin")

        if origin:
            # Have the middleware do the heavy lifting for us to parse
            # all the config, then update our response headers
            cors = (
                policy.build_middleware(_unreachable_asgi_app)
                if policy is not None
                else CORSMiddleware(app=_unreachable_asgi_app, **cls.lab_cors_kwargs())
            )

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
    def lab_cors_kwargs(cls) -> dict[str, Any]:
        """The lab default policy as ``CORSMiddleware`` keyword arguments.

        Reads ``Settings``: only call once the lab settings are loaded.
        """
        return {
            "allow_origin_regex": cls._get_allow_origin_regex(),
            "allow_credentials": cls._ALLOW_CREDENTIALS,
            "allow_methods": cls._ALLOW_METHODS,
            "allow_headers": cls._ALLOW_HEADERS,
        }

    @classmethod
    def _get_allow_origin_regex(cls) -> str:
        # in local enviornment we allow all origins
        lab_env: LabEnvironment = Settings.get_lab_environment()

        if lab_env != LabEnvironment.ON_CLOUD:
            return "." + cls._ALLOW_ANY_ORIGIN

        # In prod env we allow origin only from the virtual host (like tokyo.gencovery.io)
        virtual_host: str = Settings.get_virtual_host()

        # allow all request from sub domain or virtual host
        return r"https://.*\." + virtual_host.replace(".", r"\.")  # escape the . in virtual host
