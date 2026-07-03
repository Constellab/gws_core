from gws_core.apps.app_resource import AppResource
from gws_core.apps.apps_manager import AppsManager
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.exception.exceptions.not_found_exception import NotFoundException
from gws_core.resource.resource_model import ResourceModel
from gws_core.user.user import User


class AppGatewayService:
    """Service backing the app launcher gateway.

    The gateway entrypoint is a **front** (Angular) route ``/open/app/{app_key}``: it owns the
    auth-guard (redirecting to login when needed) and the progress UI. The backend exposes only
    JSON APIs — start (cold-start + status token) and handoff (mint the one-time code). This
    service holds their logic; authentication of the caller is resolved at the controller layer
    (lab session or a one-time code) and this service assumes an already-resolved user.
    """

    # Name of the host-only, HttpOnly cookie holding the app session JWT. Set by the app-host
    # nginx-login endpoint; read by the app (st.context.cookies / reflex request) so auth
    # survives a page reload. Mirrored as a literal in the gws_reflex_base / gws_streamlit_base
    # modules (they cannot import gws_core).
    APP_JWT_COOKIE_NAME = "gws_app_jwt"

    # Query-param name carrying the single-use handoff code in an app URL. The app relays it back
    # to the lab (POST /apps/exchange-code) to obtain the session JWT. Mirrored as a literal in
    # the gws_reflex_base / gws_streamlit_base modules (they cannot import gws_core).
    GWS_CODE_QUERY_PARAM = "gws_code"

    # Path on the app host that nginx proxies to the core-api login endpoint (which exchanges the
    # code for a JWT and sets the session cookie). Streamlit handoff targets this path.
    GWS_LOGIN_PATH = "gws-login"

    # Last URL segment of the core-api app-host login endpoint
    # (…/core-api/apps/{app_id}/nginx-login) that the app-host `GWS_LOGIN_PATH` nginx location
    # proxies to.
    NGINX_LOGIN_ENDPOINT_SEGMENT = "nginx-login"

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
    def build_app_handoff_url(cls, app_resource: AppResource, user: User) -> str:
        """Mint a one-time handoff code and build the app URL the browser is redirected to.

        Called once the app is RUNNING. The code is bound to the app; the app exchanges it for a
        JWT via POST /apps/exchange-code, then scrubs it from the URL.

        :param app_resource: the (running) app
        :param user: the authenticated user the code authenticates
        :return: the app host URL carrying ``?gws_code=<code>``
        """
        from gws_core.apps.streamlit.streamlit_process import StreamlitProcess

        app_id = app_resource.get_and_check_model_id()
        app_process = AppsManager.find_app_by_resource_model_id(app_id)
        if app_process is None or not app_process.is_running():
            raise BadRequestException("The app is not running")

        code = AppsManager.generate_app_access_code(user.id, app_id)
        host_url = app_process.get_host_url()

        # Streamlit: land on the app host's /gws-login route. nginx proxies it to the core-api
        # login endpoint, which exchanges the code for a JWT, sets the host session cookie, and
        # redirects to the app root. The code never reaches the app; the cookie carries auth and
        # survives page reloads (F5 / new tab).
        if isinstance(app_process, StreamlitProcess):
            return f"{host_url}/{cls.GWS_LOGIN_PATH}?{cls.GWS_CODE_QUERY_PARAM}={code}"

        # Reflex (and others): keep the current query-param handoff — the reflex front is a static
        # host + separate backend, so the cookie-session flow doesn't map cleanly yet. The app
        # exchanges gws_code for a JWT itself (no reload survival for now).
        return f"{host_url}?{cls.GWS_CODE_QUERY_PARAM}={code}"
