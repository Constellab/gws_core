

from typing import Dict, List

from gws_core.apps.app_dto import AppInstanceUrl, AppsStatusDTO
from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_process import AppProcess
from gws_core.apps.reflex.reflex_app import ReflexApp
from gws_core.apps.reflex.reflex_process import ReflexProcess
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.settings import Settings
from gws_core.streamlit.streamlit_app import StreamlitApp
from gws_core.streamlit.streamlit_process import StreamlitProcess


class AppPort(BaseModelDTO):
    """Class to represent a port for an app"""
    port: int = None
    host_url: str = None


class AppsManager():
    """Class to manage the different apps

    All the normal apps (without env) run in the same streamlit process (8501)
    the env apps run in different processes with different ports. One process per env.
    """

    app_dir: str = None

    # key is the env hash
    running_processes: Dict[str, AppProcess] = {}

    @classmethod
    def create_or_get_app(cls, app: AppInstance) -> AppInstanceUrl:
        cls._refresh_processes()
        # check if the app is already running in one of the processes
        for running_process in cls.running_processes.values():
            if running_process.has_app(app.app_id):
                app = running_process.get_app(app.app_id)
                return cls.get_app_full_url(app.app_id)

        cls._create_app(app)
        return cls.get_app_full_url(app.app_id)

    @classmethod
    def _create_app(cls, app: AppInstance) -> None:

        # get the env hash for this app
        env_hash: str = app.get_app_process_hash()

        # if the process for this env already exist, create the app in this process
        # no need to create a new process with a new port
        if env_hash in cls.running_processes:
            app_process = cls.running_processes[env_hash]
            app_process.add_app_to_process(app)
            return

        # create a new streamlit process
        # find available port
        # env apps run on different ports
        available_ports = cls._get_env_app_available_ports()

        if len(available_ports) == 0:
            raise Exception(
                "No available port for the app, please stop existing app in Settings > Monitoring > Others > Apps")

        # retrieve the corresponding host for the port
        front_port = available_ports[0]  # take the first available port

        # create a new process
        new_app_process: AppProcess = None
        if isinstance(app, StreamlitApp):
            new_app_process = StreamlitProcess(front_port.port, front_port.host_url, env_hash)
        elif isinstance(app, ReflexApp):
            # reflex needs both front and back ports
            if len(available_ports) < 2:
                raise Exception(
                    "No available port for the reflex app, please stop existing app in Settings > Monitoring > Others > Apps")
            back_port = available_ports[1]  # take the second available port
            new_app_process = ReflexProcess(front_port.port, front_port.host_url,
                                            back_port.port, back_port.host_url, env_hash)
        else:
            raise Exception(f"Unsupported app type: {type(app)}")

        cls.running_processes[env_hash] = new_app_process

        try:
            new_app_process.add_app_and_start_process(app)
        except Exception as e:
            cls.stop_process(env_hash)
            raise e

    @classmethod
    def _get_env_app_available_ports(cls) -> List[AppPort]:
        available_ports: List[AppPort] = []
        for app_port in cls.get_env_app_ports():
            if not cls._port_is_used(app_port.port):
                available_ports.append(app_port)
        return available_ports

    @classmethod
    def _port_is_used(cls, port: int) -> bool:
        for running_process in cls.running_processes.values():
            if running_process.uses_port(port):
                return True
        return False

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
        stopped_processes = [x for x in cls.running_processes.values() if not x.process_is_running()]

        for process in stopped_processes:
            del cls.running_processes[process.env_hash]

    @classmethod
    def get_status_dto(cls) -> AppsStatusDTO:
        cls._refresh_processes()
        return AppsStatusDTO(
            processes=[process.get_status_dto() for process in cls.running_processes.values()],
        )

    @classmethod
    def get_env_app_ports(cls) -> List[AppPort]:
        ports = Settings.get_app_ports()
        hosts = Settings.get_app_hosts()
        virtual_host = Settings.get_virtual_host()

        app_ports: List[AppPort] = []
        for i, port in enumerate(ports):
            if Settings.is_local_env():
                host_url = f"http://localhost:{port}"
            else:
                host_url = f"https://{hosts[i]}.{virtual_host}"

            app_ports.append(AppPort(port=port, host_url=host_url))
        return app_ports

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
        """Return the user id from the user access token if the user has access to the app
        """
        for running_process in cls.running_processes.values():
            if running_process.has_app(app_id):
                return running_process.user_has_access_to_app(app_id, user_access_token)

        return None

    @classmethod
    def find_app_by_resource_model_id(cls, resource_model_id: str) -> AppInstance | None:
        """Find the streamlit app that was generated from the given resource model id
        """
        for running_process in cls.running_processes.values():
            app = running_process.find_app_by_resource_model_id(resource_model_id)
            if app:
                return app

        return None
