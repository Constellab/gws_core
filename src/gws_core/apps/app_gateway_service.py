from fastapi import Request

from gws_core.apps import app_gateway_constants as _consts
from gws_core.apps.app_dto import (
    AppAccessMode,
    AppGatewayHandoffResponseDTO,
    AppGatewayStartResponseDTO,
)
from gws_core.apps.app_resource import AppResource
from gws_core.apps.apps_manager import AppsManager
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.exception.exceptions.not_found_exception import NotFoundException
from gws_core.core.exception.exceptions.unauthorized_exception import UnauthorizedException
from gws_core.core.service.front_service import FrontService
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.resource.resource_model import ResourceModel
from gws_core.user.authorization_service import AuthorizationService
from gws_core.user.user import User


class AppGatewayService:
    """Service backing the app launcher gateway.

    The gateway entrypoint is a **front** (Angular) route ``/open/app/{app_key}``: it owns the
    auth-guard (redirecting to login when needed) and the progress UI. The backend exposes only
    JSON APIs — start (cold-start + status token) and handoff (mint the one-time code). This
    service holds all their logic, including caller authentication (lab session or a one-time
    code); the controller layer only maps HTTP to the ``start`` / ``handoff`` methods below.
    """

    # Gateway/auth string constants live in the dependency-free app_gateway_constants module so
    # low-level consumers (AppProcess, nginx service) can import them without a circular dependency
    # on this service. Re-exported here as class attributes for convenience.
    APP_JWT_COOKIE_NAME = _consts.APP_JWT_COOKIE_NAME
    APP_JWT_COOKIE_MAX_AGE_SECONDS = _consts.APP_JWT_COOKIE_MAX_AGE_SECONDS
    GWS_CODE_QUERY_PARAM = _consts.GWS_CODE_QUERY_PARAM
    GWS_LOGIN_PATH = _consts.GWS_LOGIN_PATH
    NGINX_LOGIN_ENDPOINT_SEGMENT = _consts.NGINX_LOGIN_ENDPOINT_SEGMENT
    APP_FALLBACK_PATH = _consts.APP_FALLBACK_PATH
    APP_FALLBACK_ENDPOINT_SEGMENT = _consts.APP_FALLBACK_ENDPOINT_SEGMENT

    # Suffix of the Reflex state/websocket backend host ("…-back"). Stripped when mapping a host
    # back to an app key: both the front and backend hosts belong to the same app.
    _REFLEX_BACK_HOST_SUFFIX = "-back"

    @classmethod
    def app_key_from_host(cls, host: str) -> str | None:
        """Map an app host name back to its stable app key, inverting AppProcess._build_host_name.

        Used by the nginx fallback resolver: a host that matches no running app block still needs
        to be traced back to an app so the browser can be sent to the gateway.

        Handled host shapes (the port, if any, is ignored)::

            local/desktop : {segment}.localhost
            prod          : {app_sub_domain}-{segment}.{virtual_host}

        A trailing ``-back`` (the Reflex backend host) is stripped, so both hosts of a Reflex app
        resolve to the same key.

        :param host: the requested host, with or without a port
        :return: the app key (resource model id or custom subdomain), or None if the host does not
            look like an app host at all
        """
        # drop the port and normalise: host names are case-insensitive
        hostname = host.split(":", 1)[0].strip().lower()
        if not hostname:
            return None

        if Settings.is_local_or_desktop_env():
            suffix = ".localhost"
            if not hostname.endswith(suffix):
                return None
            segment = hostname[: -len(suffix)]
        else:
            virtual_host = Settings.get_virtual_host().lower()
            sub_domain = Settings.get_app_sub_domain().lower()
            host_suffix = f".{virtual_host}"
            sub_domain_prefix = f"{sub_domain}-"
            if not hostname.endswith(host_suffix):
                return None
            segment = hostname[: -len(host_suffix)]
            if not segment.startswith(sub_domain_prefix):
                return None
            segment = segment[len(sub_domain_prefix) :]

        # the Reflex backend host is the same app as its front host
        if segment.endswith(cls._REFLEX_BACK_HOST_SUFFIX):
            segment = segment[: -len(cls._REFLEX_BACK_HOST_SUFFIX)]

        return segment or None

    @classmethod
    def build_fallback_redirect_url(cls, host: str, target: str | None) -> str:
        """Build the gateway URL a request for a non-running app host is redirected to.

        Deliberately does **not** start the app or resolve a user: this runs for unauthenticated
        requests, so starting anything here would make a bare URL an app-start primitive. The
        gateway it points at owns the auth guard, the cold-start and the progress UI.

        When the host maps to no app, this returns the gateway's **error** URL rather than raising.
        The resolver is reached by a top-level browser navigation, so an API exception would render
        the raw JSON error envelope to a human. The error URL carries no app key, so the page shows
        a terminal message and never tries to start anything — the failure stays legible instead of
        bouncing into a gateway that would retry and fail confusingly.

        :param host: the originally requested app host
        :param target: the original path+query, carried so a shared deep link is not lost
        :return: the front gateway URL to redirect to (app URL, or the error URL)
        """
        front_service = FrontService()

        app_key = cls.app_key_from_host(host)
        if not app_key:
            # not shaped like an app host at all: a mistyped or foreign URL
            Logger.info(f"App fallback: host '{host}' is not an app host")
            return front_service.get_app_gateway_error_url(_consts.GATEWAY_ERROR_INVALID_HOST)

        try:
            app_resource = cls.resolve_app_resource(app_key)
        except (NotFoundException, BadRequestException):
            # well-formed key, but the app is gone (deleted) or the resource is not an app
            Logger.info(f"App fallback: no app for key '{app_key}'")
            return front_service.get_app_gateway_error_url(_consts.GATEWAY_ERROR_APP_NOT_FOUND)

        app_url = front_service.get_app_gateway_url(
            app_resource.get_and_check_model_id(), redirect_to=cls._sanitize_redirect_target(target)
        )
        Logger.debug(
            f"App fallback: host '{host}' maps to app key '{app_key}', redirecting to '{app_url}'"
        )
        return app_url

    @staticmethod
    def _sanitize_redirect_target(target: str | None) -> str | None:
        """Keep only a safe in-app path from the requested target.

        The value reaches us from an untrusted URL, so anything that could send the user to another
        origin is dropped: it must be a single-slash-prefixed path (``//host`` and absolute URLs are
        rejected). The fallback path itself is dropped to avoid redirect loops.
        """
        if not target or not target.startswith("/") or target.startswith("//"):
            return None
        if target.lstrip("/").startswith(_consts.APP_FALLBACK_PATH):
            return None
        return target

    @classmethod
    def resolve_app_resource(cls, app_key: str) -> AppResource:
        """Resolve a stable app key to its AppResource.

        The key is either the resource model id (permanent) or a custom subdomain (a readable,
        stable slug set on the app). The id is tried first; if it does not resolve, the key is
        matched against custom subdomains.

        :param app_key: resource model id or custom subdomain
        :raises NotFoundException: if no app matches the key
        :return: the resolved AppResource
        """
        resource_model = ResourceModel.get_by_id(app_key)
        if resource_model is not None:
            resource = resource_model.get_resource(resource_type=AppResource)
            if isinstance(resource, AppResource):
                return resource
            raise BadRequestException(f"Resource '{app_key}' is not an app")

        resource = cls._find_app_by_custom_subdomain(app_key)
        if resource is None:
            raise NotFoundException(f"No app found for key '{app_key}'")
        return resource

    @classmethod
    def _find_app_by_custom_subdomain(cls, subdomain: str) -> AppResource | None:
        """Find the app whose custom subdomain matches the given value, or None.

        Scans persisted app resources (app counts are modest) and compares in Python, mirroring
        the uniqueness check in AppResource._check_custom_subdomain_unique.
        """
        normalized = subdomain.lower()
        resource_models: list[ResourceModel] = list(
            ResourceModel.select_by_type_and_sub_types(AppResource)
        )
        for resource_model in resource_models:
            resource = resource_model.get_resource(resource_type=AppResource)
            if isinstance(resource, AppResource) and resource.get_custom_subdomain() == normalized:
                return resource
        return None

    @classmethod
    def start_app_and_get_status_token(cls, app_resource: AppResource) -> str:
        """(Cold-)start the app asynchronously and return the process status token.

        The token is used by the interstitial page to poll GET /apps/process/{token}/status
        until the app is RUNNING.

        Builds no app URL: the caller only polls the status, and URL generation needs a current
        user, which the lab-boot auto-start has none of.

        :param app_resource: the app to start
        :return: the process status token
        """
        app = app_resource.build_app_instance()
        app_process = AppsManager.start_app_async(app)
        return app_process.get_token()

    @classmethod
    def app_requires_authentication(cls, app_resource: AppResource) -> bool:
        """Return True when the app is AUTHENTICATED, False when it is PUBLIC (anonymous).

        A PUBLIC app is openable by anyone (no lab session or code needed); the gateway must not
        require a user for it.
        """
        return app_resource.get_access_mode() == AppAccessMode.AUTHENTICATED

    @classmethod
    def start(cls, app_key: str, code: str | None, request: Request) -> AppGatewayStartResponseDTO:
        """Resolve the caller **once**, (cold-)start the app, return the status token + a grant.

        Identity is resolved here (a one-time space ``code`` OR the lab session) and, for an
        AUTHENTICATED app, an **authorize grant** naming that user is issued and returned. The front
        replays the grant to ``handoff`` once the app is RUNNING — so handoff needs no lab session
        (a space user has none) and the identity survives the two stateless calls. A PUBLIC app is
        started for anyone and gets no grant. Raises 401 for an AUTHENTICATED app when the caller
        cannot be identified (so the front redirects to login).

        :param app_key: stable app key (resource model id or custom subdomain)
        :param code: optional one-time space access code (space/external open)
        :param request: the incoming request, used to read the lab session
        :return: the status token to poll, plus the authorize grant (None for PUBLIC)
        """
        app_resource = cls.resolve_app_resource(app_key)

        authorize_grant: str | None = None
        if cls.app_requires_authentication(app_resource):
            user = cls._resolve_gateway_user(request, code)
            if user is None:
                raise UnauthorizedException("User not authenticated")
            authorize_grant = AppsManager.generate_authorize_grant(
                user.id, app_resource.get_and_check_model_id()
            )

        status_token = cls.start_app_and_get_status_token(app_resource)
        return AppGatewayStartResponseDTO(
            status_token=status_token, authorize_grant=authorize_grant
        )

    @classmethod
    def handoff(
        cls, app_key: str, authorize_grant: str | None
    ) -> AppGatewayHandoffResponseDTO:
        """Build the app URL the browser is navigated to once the app is RUNNING.

        For an AUTHENTICATED app the user is resolved by **consuming the authorize grant** issued at
        ``start`` (no lab session required — the grant carries the identity), then a fresh, single
        app grant is minted. Minting the app grant here (post-RUNNING) keeps its short lifetime from
        expiring during cold-start. For a PUBLIC app the bare app URL is returned (anonymous).

        :param app_key: stable app key (resource model id or custom subdomain)
        :param authorize_grant: the grant returned by ``start`` (required for AUTHENTICATED apps)
        :return: the app host URL the front navigates the browser to
        """
        app_resource = cls.resolve_app_resource(app_key)

        user: User | None = None
        if cls.app_requires_authentication(app_resource):
            if not authorize_grant:
                raise UnauthorizedException("Missing authorization grant")
            app_id = app_resource.get_and_check_model_id()
            try:
                user_id = AppsManager.consume_authorize_grant(app_id, authorize_grant)
            except Exception as e:
                raise UnauthorizedException("Invalid or expired authorization grant") from e
            user = cls._get_gateway_user_by_id(user_id)

        app_url = cls.build_app_handoff_url(app_resource, user)
        return AppGatewayHandoffResponseDTO(app_url=app_url)

    @classmethod
    def _resolve_gateway_user(cls, request: Request, code: str | None) -> User | None:
        """Resolve the caller from either a one-time space code or the lab session.

        If a ``code`` is present it is consumed directly (no lab session needed); otherwise the
        lab session token (cookie/header) is tried. Returns None when neither identifies a user,
        so the gateway can bounce to the login page. The space code may name an inactive user (a
        user who reaches an app from the space without lab access), so it is resolved with
        ``allow_inactive=True``.
        """
        if code:
            return AuthorizationService.check_unique_code(code, allow_inactive=True).get_user()

        try:
            return AuthorizationService.check_user_access_token(request).get_user()
        except Exception:
            return None

    @classmethod
    def _get_gateway_user_by_id(cls, user_id: str) -> User:
        """Resolve a user id (from a consumed authorize grant) to a User for the gateway.

        Allows an inactive user: a space visitor may have no lab login. The identity was already
        vouched for at ``start`` (space code or lab session) and carried in the single-use grant.
        """
        return AuthorizationService._get_and_check_user(user_id, allow_inactive=True)

    @classmethod
    def build_app_handoff_url(cls, app_resource: AppResource, user: User | None) -> str:
        """Build the app URL the browser is redirected to once the app is RUNNING.

        For an AUTHENTICATED app a one-time handoff code (bound to the app + user) is minted; the
        app exchanges it for a JWT via POST /apps/exchange-code, then scrubs it from the URL. For a
        PUBLIC app (``user`` is None) the URL is bare — the app runs anonymously, exactly as when
        it is opened directly, so no code is minted.

        :param app_resource: the (running) app
        :param user: the authenticated user the code authenticates, or None for a PUBLIC app
        :return: the app host URL (carrying ``?gws_code=<code>`` for AUTHENTICATED apps)
        """

        app_id = app_resource.get_and_check_model_id()
        app_process = AppsManager.find_app_by_resource_model_id(app_id)
        if app_process is None or not app_process.is_running():
            raise BadRequestException("The app is not running")

        host_url = app_process.get_host_url()

        # PUBLIC app: no user, no code — the app runs anonymously on a bare URL.
        if user is None:
            return host_url

        code = AppsManager.generate_app_access_code(user.id, app_id)

        # How the code is conveyed to the app depends on the framework (Streamlit lands on the
        # nginx /gws-login route for a cookie session; Reflex keeps the query-param handoff), so
        # each process subclass builds its own handoff URL.
        return app_process.build_handoff_url(host_url, code)
