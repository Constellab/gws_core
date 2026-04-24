import os
import signal
from datetime import datetime, timedelta

from gws_core.apps.app_dto import AppInstanceUrl, AppsStatusDTO, CreateAppAsyncResultDTO
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
        """
        if start_port is None:
            start_port = Settings.get_app_external_port() + 1

        while cls._port_is_used(start_port):
            start_port += 1

        return start_port

    @classmethod
    def _port_is_used(cls, port: int) -> bool:
        for running_process in cls.running_processes.values():
            if running_process.uses_port(port):
                return True
        return False

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
                        previous(signum, frame)
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
    def set_disable_auto_stop(cls, app_id: str, disable_auto_stop: bool) -> None:
        """Set the disable_auto_stop option on an app resource and update the running process if any.

        :param app_id: the resource model id of the app
        :param disable_auto_stop: True to disable automatic stop when no connections are detected
        """

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(app_id)
        resource: AppResource = resource_model.get_resource()

        if not isinstance(resource, AppResource):
            raise BadRequestException(f"Resource with ID {app_id} is not an AppResource")

        resource.set_disable_auto_stop(disable_auto_stop)
        resource_model.update_resource_fields(resource)

        # Update the running process if the app is currently running
        app_process = cls.find_app_by_resource_model_id(app_id)
        if app_process is not None:
            app_process.set_disable_auto_stop(disable_auto_stop)

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
