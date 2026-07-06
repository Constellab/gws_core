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
    GWS_CODE_QUERY_PARAM = _consts.GWS_CODE_QUERY_PARAM
    GWS_LOGIN_PATH = _consts.GWS_LOGIN_PATH
    NGINX_LOGIN_ENDPOINT_SEGMENT = _consts.NGINX_LOGIN_ENDPOINT_SEGMENT

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

        :param app_resource: the app to start
        :return: the process status token
        """
        app = app_resource.build_app_instance()
        AppsManager.create_or_get_app_async(app)

        app_process = AppsManager.find_app_by_resource_model_id(app.resource_model_id)
        if app_process is None:
            raise BadRequestException("The app failed to start")
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
