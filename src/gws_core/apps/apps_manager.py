import os
import signal
import socket
from datetime import datetime, timedelta

from gws_core.apps.app_dto import (
    AppInstanceUrl,
    AppsStatusDTO,
    AppStopPolicy,
    CreateAppAsyncResultDTO,
    ExchangeAppCodeResponseDTO,
    ValidateAppJwtResponseDTO,
)
from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_nginx_manager import AppNginxManager
from gws_core.apps.app_process import AppProcess
from gws_core.apps.app_resource import AppResource
from gws_core.apps.reflex.reflex_app import ReflexApp
from gws_core.apps.reflex.reflex_process import ReflexProcess
from gws_core.apps.streamlit.streamlit_app import StreamlitApp
from gws_core.apps.streamlit.streamlit_process import StreamlitProcess
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import LogContext
from gws_core.core.utils.settings import Settings
from gws_core.lab.log.log import LogsBetweenDates
from gws_core.lab.log.log_service import LogService
from gws_core.resource.resource_model import ResourceModel
from gws_core.user.jwt_service import JWTService
from gws_core.user.unique_code_service import InvalidUniqueCodeException, UniqueCodeService
from gws_core.user.user_exception import InvalidTokenException


class AppsManager:
    """Class to manage the different apps.

    Each app runs in its own dedicated process.
    """

    app_dir: str | None = None

    # key is the app resource model id
    running_processes: dict[str, AppProcess] = {}

    MAX_RUNNING_APPS = 50

    @classmethod
    def create_or_get_app(cls, app: AppInstance) -> AppInstanceUrl:
        app_process = cls._create_or_get_app_async(app)

        app_process.wait_for_start()

        if not app_process.is_running():
            raise Exception("App failed to start")

        return app_process.get_app_full_url()

    @classmethod
    def create_or_get_app_async(cls, app: AppInstance) -> CreateAppAsyncResultDTO:
        """Create app asynchronously and return the app ID. The app will be started in background."""
        # Create or get process and add app to it
        app_process = cls._create_or_get_app_async(app)

        get_status_route = (
            f"{Settings.get_lab_api_url()}/{Settings.core_api_route_path()}/apps/process/"
            + f"{app_process.get_token()}/status"
        )

        return CreateAppAsyncResultDTO(
            app_id=app.resource_model_id,
            app_url=app_process.get_app_full_url(),
            get_status_route=get_status_route,
            status=app_process.get_status(),
            status_text=app_process.get_status_text(),
        )

    @classmethod
    def _create_or_get_app_async(cls, app: AppInstance) -> AppProcess:
        """Create app asynchronously and return the app ID. The app will be registered and started in background."""
        cls._refresh_processes()

        # Create or get process and set app for it
        app_process = cls._register_app_and_process(app)

        app_process.start_app_async()

        return app_process

    @classmethod
    def _register_app_and_process(cls, app: AppInstance) -> AppProcess:
        """Create or get process and set the app for it"""
        app_id: str = app.resource_model_id

        app_process = cls.running_processes.get(app_id)

        # register the process if it does not exist
        if not app_process:
            # check number of running apps
            if len(cls.running_processes) >= cls.MAX_RUNNING_APPS:
                raise Exception(
                    f"Maximum number of running apps reached ({cls.MAX_RUNNING_APPS}). "
                    "Please stop some apps before starting new ones."
                )

            # retrieve the corresponding host for the port
            front_port = cls._get_next_available_port()  # take the first available port

            # create a new process with assigned ports
            if isinstance(app, StreamlitApp):
                app_process = StreamlitProcess(front_port, app)
            elif isinstance(app, ReflexApp):
                back_port = cls._get_next_available_port(
                    front_port + 1
                )  # take the next available port for the backend
                # for reflex app, we need both front and back ports
                # the id is set as the resource model id because 1 Process = 1 app
                # and the id is used to build the app front and back URL and the url must not change
                # when the app is restarted (because back url is in front build)
                app_process = ReflexProcess(front_port, back_port, app)
            else:
                raise Exception(f"Unsupported app type: {type(app)}")

            # Register the process
            cls.running_processes[app_id] = app_process

        return app_process

    @classmethod
    def _get_next_available_port(cls, start_port: int | None = None) -> int:
        """Get the next available port for an app.
        This is used to find a port for the env apps.

        A port is considered usable only if it is neither tracked by one of
        this process's running app processes *nor* actually bound at the OS
        level — under parallel tests (pytest-xdist) a previous app on this
        worker may still be shutting down, or a neighbouring worker may hold a
        port in our band.
        """
        if start_port is None:
            start_port = Settings.get_app_external_port() + 1

        while cls._port_is_used(start_port) or cls._port_is_bound(start_port):
            start_port += 1

        return start_port

    @classmethod
    def _port_is_used(cls, port: int) -> bool:
        for running_process in cls.running_processes.values():
            if running_process.uses_port(port):
                return True
        return False

    @classmethod
    def _port_is_bound(cls, port: int) -> bool:
        """Return True if something is currently listening on ``port`` (OS-level)."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            return sock.connect_ex(("localhost", port)) == 0

    @classmethod
    def init(cls):
        cls._register_signal_handlers()
        AppNginxManager.init()

    @classmethod
    def _register_signal_handlers(cls) -> None:
        """Register SIGINT/SIGTERM handlers as a safety net to stop child app
        processes even when graceful shutdown hooks (e.g. FastAPI lifespan)
        do not run — notably the dev CLIs (`gws reflex run`, `gws streamlit run`)
        which never start a FastAPI server, and abrupt server terminations.

        The handler chains to the previous handler so uvicorn's own graceful
        shutdown path still runs in server mode.
        """
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous = signal.getsignal(sig)

            # Only chain to previous handler if it's a real custom handler
            # (e.g. uvicorn's graceful-shutdown handler). Skip Python defaults
            # (SIG_DFL, SIG_IGN, default_int_handler) — chaining to
            # default_int_handler would raise KeyboardInterrupt during
            # interpreter shutdown and print an "Exception ignored" traceback.
            should_chain = (
                callable(previous)
                and previous not in (signal.SIG_DFL, signal.SIG_IGN)
                and previous is not signal.default_int_handler
            )

            def handler(signum, frame, previous=previous, should_chain=should_chain):
                try:
                    cls.stop_all_processes()
                finally:
                    if should_chain:
                        previous(signum, frame)  # type: ignore
                    else:
                        # os._exit skips interpreter finalizers; safer than
                        # sys.exit when the handler may fire during
                        # threading._shutdown (cleanup is already done above).
                        os._exit(0)

            signal.signal(sig, handler)

    @classmethod
    def stop_all_processes(cls) -> None:
        for running_process in cls.running_processes.values():
            running_process.stop_process()

        cls.running_processes = {}

    @classmethod
    def stop_process(cls, app_id: str) -> None:
        if app_id in cls.running_processes:
            cls.running_processes[app_id].stop_process()
            del cls.running_processes[app_id]

    ############################# OTHERS ####################################

    @classmethod
    def _refresh_processes(cls) -> None:
        """Method to remove the stopped processes from the running_processes dict.
        Because if it is killed after inactivity, the AppsManager does not know it.
        """
        stopped_processes = [x for x in cls.running_processes.values() if x.is_stopped()]

        for process in stopped_processes:
            del cls.running_processes[process.get_id()]

    @classmethod
    def get_status_dto(cls) -> AppsStatusDTO:
        cls._refresh_processes()
        return AppsStatusDTO(
            processes=[process.get_status_dto() for process in cls.running_processes.values()],
        )

    @classmethod
    def get_app_dir(cls) -> str:
        if cls.app_dir is None:
            cls.app_dir = Settings.make_temp_dir()
        return cls.app_dir

    @classmethod
    def user_has_access_to_app(cls, app_id: str, user_access_token: str) -> str | None:
        """Return the user id from the user access token if the user has access to the app"""
        app = cls.find_app_by_resource_model_id(app_id)
        if app is not None:
            return app.user_has_access_to_app(user_access_token)

        return None

    # key stored in the code obj to bind a one-time app code to a single app
    APP_CODE_APP_ID_KEY = "app_id"

    # Validity of the app code when it is baked into the app URL up front (datalab iframe /
    # get_app_full_url), BEFORE the app has started. A Reflex app builds its frontend bundle on
    # first start (can take minutes), and the app only exchanges the code AFTER that — so a 60 s
    # code would already be expired (403 "Invalid url"). This window must outlast a cold build.
    # (The gateway handoff mints its code post-RUNNING and navigates immediately, so it keeps the
    # tight 60 s default.)
    URL_APP_CODE_VALIDITY_SECONDS = 60 * 10  # 10 min: covers a cold Reflex frontend build

    # Authorize grant: the single-use carrier the gateway issues at `authorize` (start) and the
    # front replays at `handoff`. It names the resolved user and is bound to the app, so handoff can
    # re-resolve the user WITHOUT a lab session (a space user has none) and mint the fresh app grant
    # only once the app is RUNNING. Distinct payload key from the app grant so the two are not
    # interchangeable. Its lifetime must outlast a cold-start + status polling (see
    # AUTHORIZE_GRANT_VALIDITY_SECONDS). See APP_AUTH_OAUTH_REDESIGN.md.
    AUTHORIZE_GRANT_APP_ID_KEY = "authorize_app_id"
    AUTHORIZE_GRANT_VALIDITY_SECONDS = 60 * 10  # 10 min: comfortably covers cold-start + polling

    @classmethod
    def generate_authorize_grant(cls, user_id: str, app_id: str) -> str:
        """Mint the single-use authorize grant returned by the gateway ``authorize`` step.

        Names the resolved user and is bound to ``app_id``. The front replays it to ``handoff``,
        which consumes it (``consume_authorize_grant``) to re-resolve the user without a lab
        session and mint the fresh app grant post-RUNNING.

        :param user_id: the user resolved at authorize (lab session or space code)
        :param app_id: the app the grant is bound to
        :return: the one-time authorize grant
        """
        return UniqueCodeService.generate_code(
            user_id,
            {cls.AUTHORIZE_GRANT_APP_ID_KEY: app_id},
            cls.AUTHORIZE_GRANT_VALIDITY_SECONDS,
        )

    @classmethod
    def consume_authorize_grant(cls, app_id: str, grant: str) -> str:
        """Consume an authorize grant and return the user id it names.

        Confirms the grant was minted for this app before trusting it, so a grant for app A cannot
        be replayed on app B.

        :param app_id: the app the grant must be bound to
        :param grant: the single-use authorize grant (consumed here)
        :return: the user id the grant names
        :raises InvalidUniqueCodeException: if the grant is invalid, expired, or for another app
        """
        code_obj = UniqueCodeService.check_code(grant)
        if code_obj.obj.get(cls.AUTHORIZE_GRANT_APP_ID_KEY) != app_id:
            raise InvalidUniqueCodeException()
        return code_obj.user_id

    @classmethod
    def generate_app_access_code(cls, user_id: str, app_id: str, validity_seconds: int = 60) -> str:
        """Mint a short-lived, single-use code that authenticates a user to a specific app.

        The code is put in the app URL as ``gws_code``. The app relays it back to
        ``exchange_app_code`` (it cannot consume the code itself, being gws_core-free), which
        swaps it for a JWT. The code is bound to ``app_id`` so it cannot be replayed against
        another app.

        :param user_id: the user the code authenticates
        :param app_id: the app resource model id the code is valid for
        :param validity_seconds: code lifetime (single-use). Default 60s suits the gateway handoff
            (minted post-RUNNING, navigated immediately); pass URL_APP_CODE_VALIDITY_SECONDS when
            baking the code into the app URL up front (must survive a cold build before exchange).
        :return: the one-time code
        """
        return UniqueCodeService.generate_code(
            user_id, {cls.APP_CODE_APP_ID_KEY: app_id}, validity_seconds
        )

    @classmethod
    def exchange_app_code(cls, app_id: str, code: str) -> ExchangeAppCodeResponseDTO:
        """Consume a one-time app code and return a JWT + the resolved user id.

        Called from the app (via POST /apps/exchange-code) to turn the ``gws_code`` it received
        in its URL into a JWT it carries on data lab API calls. The code is single-use
        (consumed here) and must match the app it was minted for.

        :param app_id: the app the code is being exchanged for (must match the code binding)
        :param code: the one-time code from the app URL
        :return: the JWT (as user_access_token) and the user id
        :raises InvalidUniqueCodeException: if the code is invalid, expired, or for another app
        """
        code_obj = UniqueCodeService.check_code(code)

        # bind the code to its app: reject a code minted for a different app
        if code_obj.obj.get(cls.APP_CODE_APP_ID_KEY) != app_id:
            raise InvalidUniqueCodeException()

        # Mint an app-scoped token (typ:app, app_id) — NOT a general session JWT. It authenticates
        # the user only for this app's API calls and is rejected on normal user routes. See
        # APP_AUTH_OAUTH_REDESIGN.md.
        return ExchangeAppCodeResponseDTO(
            user_access_token=JWTService.create_app_jwt(code_obj.user_id, app_id),
            user_id=code_obj.user_id,
        )

    @classmethod
    def validate_app_jwt(cls, app_id: str, jwt: str) -> ValidateAppJwtResponseDTO:
        """Validate an app-scoped token (from the app's ``gws_app_jwt`` cookie) and return the user id.

        Used on a fresh page load (F5 / new tab) to re-authenticate without a one-time code: the
        app stored the app token in a cookie on first load and relays it here. Validated as an
        app-scoped token bound to this app (typ:app + matching app_id), so a token minted for
        another app is rejected.

        :param app_id: the app the token must be scoped to
        :param jwt: the token (with or without the ``Bearer `` prefix)
        :return: the resolved user id
        :raises InvalidTokenException: if the token is missing, malformed, expired, or not scoped
            to this app
        """
        # JWTService expects the "Bearer " scheme prefix; add it if the cookie stored the bare token.
        token = jwt if jwt.startswith(JWTService.AUTH_SCHEME) else JWTService.AUTH_SCHEME + jwt
        try:
            user_id = JWTService.check_app_access_token(token, app_id)
        except Exception as e:
            # normalize any JWT-library decode/verify error into a clean typed exception
            # (so the endpoint returns 401, not an uncaught 500)
            raise InvalidTokenException() from e
        return ValidateAppJwtResponseDTO(user_id=user_id)

    @classmethod
    def find_process_by_token(cls, token: str) -> AppProcess | None:
        """Find the process that contains the app with the given token"""
        for running_process in cls.running_processes.values():
            if running_process.get_token() == token:
                return running_process

        return None

    @classmethod
    def find_app_by_resource_model_id(cls, resource_model_id: str) -> AppProcess | None:
        """Find the streamlit app that was generated from the given resource model id"""
        return cls.running_processes.get(resource_model_id)

    @classmethod
    def set_stop_policy(cls, app_id: str, stop_policy: AppStopPolicy) -> None:
        """Set the stop policy on an app resource and update the running process if any.

        :param app_id: the resource model id of the app
        :param stop_policy: the stop policy to apply
        """

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(app_id)
        resource = resource_model.get_resource(resource_type=AppResource)

        if not isinstance(resource, AppResource):
            raise BadRequestException(f"Resource with ID {app_id} is not an AppResource")

        resource.set_stop_policy(stop_policy)
        resource_model.update_resource_fields(resource)

        # Update the running process if the app is currently running
        app_process = cls.find_app_by_resource_model_id(app_id)
        if app_process is not None:
            app_process.set_stop_policy(stop_policy)

    @classmethod
    def set_custom_subdomain(cls, app_id: str, subdomain: str | None) -> None:
        """Set (or clear) the custom subdomain on an app resource.

        The value is validated and checked for DB-wide uniqueness by the resource setter.
        Passing a falsy value clears the custom subdomain and restores the default id-based host.

        The custom subdomain is a front-only alias on the app host: the canonical id-based host
        is kept, and the custom host is added as an extra nginx server_name. If the app is
        currently running, the change is applied immediately (the front nginx service is
        re-registered and nginx reloaded); otherwise it takes effect on the next start.

        :param app_id: the resource model id of the app
        :param subdomain: the custom subdomain to apply, or None/"" to clear it
        :raises BadRequestException: if the resource is not an AppResource, or the value is
                                     invalid or already used by another app
        """

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(app_id)
        resource = resource_model.get_resource(resource_type=AppResource)

        if not isinstance(resource, AppResource):
            raise BadRequestException(f"Resource with ID {app_id} is not an AppResource")

        resource.set_custom_subdomain(subdomain)
        resource_model.update_resource_fields(resource)

        # Apply live to the running process if any (re-registers nginx with the new alias)
        app_process = cls.find_app_by_resource_model_id(app_id)
        if app_process is not None:
            app_process.update_custom_subdomain(resource.get_custom_subdomain())

    @classmethod
    def get_logs_of_app(
        cls, app_id: str, from_page_date: datetime | None = None
    ) -> LogsBetweenDates:
        """Read the server log filtered by the app id

        :param app_id: the resource model id of the app
        :param from_page_date: the date to start reading from (for pagination)
        :return: LogsBetweenDates object containing the logs
        """
        app_process = cls.find_app_by_resource_model_id(app_id)

        if app_process is None:
            raise BadRequestException(f"App with ID {app_id} not found")

        # Determine the log context based on the app type
        context = None
        if isinstance(app_process, StreamlitProcess):
            context = LogContext.STREAMLIT
        elif isinstance(app_process, ReflexProcess):
            context = LogContext.REFLEX
        else:
            raise BadRequestException(f"Unsupported app type: {type(app_process)}")

        # Use a reasonable time window - apps don't have exact start times stored
        # So we'll get logs from a reasonable time ago (e.g., 24 hours)
        start_date: datetime = from_page_date or DateHelper.now_utc() - timedelta(hours=24)

        end_date = DateHelper.now_utc()

        # Retrieve the log generated by the app
        return LogService.get_logs_between_dates(
            start_date, end_date, context=context, context_id=app_id
        )
