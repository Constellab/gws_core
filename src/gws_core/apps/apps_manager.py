import signal
import sys
from datetime import datetime, timedelta

from gws_core.apps.app_dto import AppInstanceUrl, AppsStatusDTO, CreateAppAsyncResultDTO
from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_nginx_manager import AppNginxManager
from gws_core.apps.app_process import AppProcess
from gws_core.apps.reflex.reflex_app import ReflexApp
from gws_core.apps.reflex.reflex_process import ReflexProcess
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import LogContext
from gws_core.core.utils.settings import Settings
from gws_core.lab.log.log import LogsBetweenDates
from gws_core.lab.log.log_service import LogService
from gws_core.streamlit.streamlit_app import StreamlitApp
from gws_core.streamlit.streamlit_process import StreamlitProcess


class AppPort(BaseModelDTO):
    """Class to represent a port for an app"""

    port: int = None
    host_url: str = None


class AppsManager:
    """Class to manage the different apps

    All the normal apps (without env) run in the same streamlit process (8501)
    the env apps run in different processes with different ports. One process per env.
    """

    app_dir: str = None

    # key is the env hash
    running_processes: dict[str, AppProcess] = {}

    MAX_RUNNING_APPS = 50

    @classmethod
    def create_or_get_app(cls, app: AppInstance) -> AppInstanceUrl:
        app_process = cls._create_or_get_app_async(app)

        app_process.wait_for_start()

        if not app_process.is_running():
            raise Exception("App failed to start")

        return cls.get_app_full_url(app.resource_model_id)

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
            app_url=app_process.get_app_full_url(app.resource_model_id),
            get_status_route=get_status_route,
            status=app_process.get_status(),
            status_text=app_process.get_status_text(),
        )

    @classmethod
    def _create_or_get_app_async(cls, app: AppInstance) -> AppProcess:
        """Create app asynchronously and return the app ID. The app will be registered and started in background."""
        cls._refresh_processes()

        # Create or get process and add app to it
        app_process = cls._register_app_and_process(app)

        app_process.start_app_async(app.resource_model_id)

        return app_process

    @classmethod
    def _register_app_and_process(cls, app: AppInstance) -> AppProcess:
        """Create or get process and add app to it if not exists"""
        # get the env hash for this app
        env_hash: str = app.get_app_process_hash()

        app_process = cls.running_processes.get(env_hash)

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
                app_process = StreamlitProcess(front_port, app.resource_model_id, env_hash)
            elif isinstance(app, ReflexApp):
                back_port = cls._get_next_available_port(
                    front_port + 1
                )  # take the next available port for the backend
                # for reflex app, we need both front and back ports
                # also we set the id as the resource model id because 1 Process = 1 app
                # and the id is used to build the app front and back URL and the url must not change
                # when the app is restarted (because back url is in front build)
                app_process = ReflexProcess(front_port, back_port, app.resource_model_id, env_hash)
            else:
                raise Exception(f"Unsupported app type: {type(app)}")

        # Add the app to the process if it does not exist
        app_process.add_app_if_not_exists(app)

        # Add the app to the process and register the process
        cls.running_processes[env_hash] = app_process

        return app_process

    @classmethod
    def _get_next_available_port(cls, start_port: int = None) -> int:
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
        """Register signal handlers to gracefully stop all processes on exit"""

        def signal_handler(sig, frame):
            print("Stopping all app processes before exit...")
            cls.stop_all_processes()
            sys.exit(0)

        # Register handlers for common termination signals
        signal.signal(signal.SIGINT, signal_handler)  # CTRL+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination request

        AppNginxManager.init()

    @classmethod
    def stop_all_processes(cls) -> None:
        for running_process in cls.running_processes.values():
            running_process.stop_process()

        cls.running_processes = {}

    @classmethod
    def stop_process(cls, env_hash: str) -> None:
        if env_hash in cls.running_processes:
            cls.running_processes[env_hash].stop_process()
            del cls.running_processes[env_hash]

    ############################# OTHERS ####################################

    @classmethod
    def _refresh_processes(cls) -> None:
        """Method to remove the stopped processes from the running_processes dict.
        Because if it is killed after inactivity, the APpManager does not know it.
        """
        stopped_processes = [x for x in cls.running_processes.values() if x.is_stopped()]

        for process in stopped_processes:
            del cls.running_processes[process.env_hash]

    @classmethod
    def get_status_dto(cls) -> AppsStatusDTO:
        cls._refresh_processes()
        return AppsStatusDTO(
            processes=[process.get_status_dto() for process in cls.running_processes.values()],
        )

    @classmethod
    def get_app_full_url(cls, app_id: str) -> AppInstanceUrl:
        for running_process in cls.running_processes.values():
            if running_process.has_app(app_id):
                return running_process.get_app_full_url(app_id)

        raise Exception(f"App {app_id} not found")

    @classmethod
    def get_app_dir(cls) -> str:
        if cls.app_dir is None:
            cls.app_dir = Settings.make_temp_dir()
        return cls.app_dir

    @classmethod
    def user_has_access_to_app(cls, app_id: str, user_access_token: str) -> str | None:
        """Return the user id from the user access token if the user has access to the app"""
        for running_process in cls.running_processes.values():
            if running_process.has_app(app_id):
                return running_process.user_has_access_to_app(app_id, user_access_token)

        return None

    @classmethod
    def find_process_of_app(cls, resource_model_id: str) -> AppProcess | None:
        """Find the process that contains the app with the given resource model id"""
        for running_process in cls.running_processes.values():
            if running_process.has_app(resource_model_id):
                return running_process

        return None

    @classmethod
    def find_process_by_token(cls, token: str) -> AppProcess | None:
        """Find the process that contains the app with the given token"""
        for running_process in cls.running_processes.values():
            if running_process.get_token() == token:
                return running_process

        return None

    @classmethod
    def find_app_by_resource_model_id(cls, resource_model_id: str) -> AppInstance | None:
        """Find the streamlit app that was generated from the given resource model id"""
        for running_process in cls.running_processes.values():
            app = running_process.find_app_by_resource_model_id(resource_model_id)
            if app:
                return app

        return None

    @classmethod
    def get_logs_of_app(cls, app_id: str, from_page_date: datetime = None) -> LogsBetweenDates:
        """Read the server log filtered by the app id

        :param app_id: the resource model id of the app
        :param from_page_date: the date to start reading from (for pagination)
        :return: LogsBetweenDates object containing the logs
        """
        app = cls.find_app_by_resource_model_id(app_id)

        if app is None:
            raise BadRequestException(f"App with ID {app_id} not found")

        # Determine the log context based on the app type
        context = None
        if isinstance(app, StreamlitApp):
            context = LogContext.STREAMLIT
        elif isinstance(app, ReflexApp):
            context = LogContext.REFLEX
        else:
            raise BadRequestException(f"Unsupported app type: {type(app)}")

        # Use a reasonable time window - apps don't have exact start times stored
        # So we'll get logs from a reasonable time ago (e.g., 24 hours)
        start_date: datetime = None
        if from_page_date:
            start_date = from_page_date
        else:
            # Get logs from the last 24 hours
            start_date = DateHelper.now_utc() - timedelta(hours=24)

        end_date = DateHelper.now_utc()

        # Retrieve the log generated by the app
        return LogService.get_logs_between_dates(
            start_date, end_date, context=context, context_id=app_id
        )
