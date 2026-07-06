from datetime import datetime
from enum import Enum

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.user.user_dto import UserDTO


class AppType(Enum):
    STREAMLIT = "STREAMLIT"
    REFLEX = "REFLEX"


class AppStopPolicy(Enum):
    """Defines how an app process is stopped when no connections are detected."""

    # The app is automatically stopped when no connections are detected (default).
    AUTO = "AUTO"
    # The app stays alive until it is explicitly stopped.
    MANUAL = "MANUAL"


class AppAccessMode(Enum):
    """Defines who can access an app and what identity its backend calls run as.

    - AUTHENTICATED: only the user that launched the app can open it (a token is added to
      the URL). Backend API calls run as that real user. This is the default.
    - PUBLIC: anyone with the link can open the app (the URL is bare, no token). The app
      runs anonymously: no user is authenticated and backend calls carry no user identity.
    """

    AUTHENTICATED = "AUTHENTICATED"
    PUBLIC = "PUBLIC"


class AppInstanceUrl(BaseModelDTO):
    host_url: str

    params: dict[str, str] | None = None

    def get_url(self) -> str:
        url = self.host_url

        if self.params is not None and len(self.params) > 0:
            params = "&".join([f"{key}={value}" for key, value in self.params.items()])
            url += f"?{params}"
        return url

    def add_param(self, key: str, value: str) -> None:
        if self.params is None:
            self.params = {}
        self.params[key] = value


class AppInstanceDTO(BaseModelDTO):
    app_type: AppType
    app_resource_id: str
    name: str
    env_type: str
    stop_policy: AppStopPolicy = AppStopPolicy.AUTO
    custom_subdomain: str | None = None
    source_ids: list[str] | None = None
    env_file_path: str | None = None  # for env app
    env_file_content: str | None = None  # for env app


class AppProcessStatus(Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"


class CreateAppAsyncResultDTO(BaseModelDTO):
    app_id: str
    app_url: AppInstanceUrl
    get_status_route: str
    status: AppProcessStatus
    status_text: str | None = None


class AppProcessLightStatusDTO(BaseModelDTO):
    """Minimal status returned by the token-guarded polling route
    (GET /apps/process/{token}/status).

    The polling token is an opaque process handle, not a user credential, so the payload is kept to
    the lifecycle fields the gateway progress UI needs — no user, config path, env content, or
    source ids (which the rich AppProcessStatusDTO on the authenticated /apps/status route exposes).
    See APP_AUTH_OAUTH_REDESIGN.md.
    """

    id: str
    status: AppProcessStatus
    status_text: str | None = None


class AppProcessStatusDTO(BaseModelDTO):
    id: str
    status: AppProcessStatus
    status_text: str | None = None
    app: AppInstanceDTO
    nb_of_connections: int
    config_file_path: str
    started_at: datetime | None
    started_by: UserDTO | None
    # Bare host URL (scheme + host + port, no auth token) reachable via the app's custom
    # subdomain alias. None when the app has no custom subdomain (or in dev mode).
    custom_subdomain_url: str | None = None


class AppsStatusDTO(BaseModelDTO):
    processes: list[AppProcessStatusDTO]


class AppInstanceConfigDTO(BaseModelDTO):
    source_ids: list[str]
    params: dict | None
    # List of token of user that can access the app
    # Only provided if the app requires authentication
    # Key is access token, value is user id
    user_access_tokens: dict[str, str]


class ExchangeAppCodeDTO(BaseModelDTO):
    """Body of POST /apps/exchange-code: a one-time code the app relays to the lab.

    The app (reflex/streamlit base) cannot import gws_core, so it cannot consume the code
    or mint a JWT itself. It sends the code here and gets back a JWT + the resolved user id.
    """

    app_id: str
    code: str


class ExchangeAppCodeResponseDTO(BaseModelDTO):
    """Response of POST /apps/exchange-code.

    :user_access_token: a JWT the app carries on its data lab API calls (validated by the
        existing check_user_access_token). Replaces the former opaque user access token.
    :user_id: the resolved user id, so the app can display the user without decoding the JWT
        (it has no access to the JWT secret).
    """

    user_access_token: str
    user_id: str


class AppGatewayStartDTO(BaseModelDTO):
    """Body of POST /apps/gateway/start, called by the front (Angular) gateway page.

    :app_key: the stable app key (resource model id or custom subdomain)
    :code: optional one-time code (space/external open); when absent the caller is resolved
        from the lab session cookie.
    """

    app_key: str
    code: str | None = None


class AppGatewayStartResponseDTO(BaseModelDTO):
    """Response of POST /apps/gateway/start.

    :status_token: the process status token the front polls on
        GET /apps/process/{status_token}/status until the app is RUNNING.
    :authorize_grant: for an AUTHENTICATED app, a single-use grant naming the resolved caller,
        bound to the app. The front keeps it and replays it to POST /apps/gateway/handoff once the
        app is RUNNING (a space caller has no lab session, and the space code is consumed here, so
        this grant is how the identity is carried to handoff). None for a PUBLIC app.
    """

    status_token: str
    authorize_grant: str | None = None


class AppGatewayHandoffDTO(BaseModelDTO):
    """Body of POST /apps/gateway/handoff, called by the front once the app is RUNNING.

    :app_key: the stable app key (resource model id or custom subdomain)
    :authorize_grant: the grant returned by /apps/gateway/start, replayed here to identify the
        caller without a lab session (AUTHENTICATED apps). None for a PUBLIC app.
    """

    app_key: str
    authorize_grant: str | None = None


class AppGatewayHandoffResponseDTO(BaseModelDTO):
    """Response of POST /apps/gateway/handoff.

    :app_url: the app host URL carrying a one-time ``gws_code`` the app exchanges for a JWT.
        The front navigates the browser to this URL.
    """

    app_url: str


class ValidateAppJwtDTO(BaseModelDTO):
    """Body of POST /apps/validate-jwt.

    On a fresh page load (F5 / new tab), the app has no one-time code but holds the JWT it
    stored in a cookie on first load. It relays the JWT here to re-authenticate. The app cannot
    validate the JWT itself (no gws_core, no secret).

    :app_id: the app the JWT is being used for (must match the code the JWT was minted from)
    :jwt: the JWT stored in the ``gws_app_jwt`` cookie (with or without the ``Bearer `` prefix)
    """

    app_id: str
    jwt: str


class ValidateAppJwtResponseDTO(BaseModelDTO):
    """Response of POST /apps/validate-jwt: the resolved user id for a valid JWT."""

    user_id: str
