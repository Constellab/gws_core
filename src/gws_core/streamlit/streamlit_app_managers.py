

from typing import Dict, List

from gws_core.core.utils.settings import Settings
from gws_core.streamlit.streamlit_app import StreamlitApp
from gws_core.streamlit.streamlit_dto import StreamlitStatusDTO
from gws_core.streamlit.streamlit_process import StreamlitProcess


class StreamlitAppManager():
    """Class to manage the different streamlit processes and apps

    All the normal apps (without env) run in the same streamlit process (8501)
    the env apps run in different processes with different ports. One process per env.
    """

    app_dir: str = None

    # key is the env hash
    running_processes: Dict[str, StreamlitProcess] = {}

    @classmethod
    def create_or_get_app(cls, app: StreamlitApp) -> str:
        for streamlit_process in cls.running_processes.values():
            if streamlit_process.has_app(app.app_id):
                streamlit_process.get_app(app.app_id)

        cls._create_app(app)
        return cls.get_app_full_url(app.app_id)

    @classmethod
    def _create_app(cls, app: StreamlitApp) -> None:

        # get the env hash for this app
        env_hash: str = app.get_env_code_hash()

        # if the process for this env already exist, create the app in this process
        # no need to create a new process with a new port
        if env_hash in cls.running_processes:
            streamlit_process = cls.running_processes[env_hash]
            streamlit_process.create_app(app)
            return

        # create a new streamlit process
        # find available port
        port: int = None
        # all normal apps run on the same port
        if app.is_normal_app():
            port = cls.get_main_app_port()
        else:
            # env apps run on different ports
            port = cls._get_env_app_available_port()

        # create a new process
        streamlit_process = StreamlitProcess(port, app.app_type, app.env_code, env_hash)
        cls.running_processes[env_hash] = streamlit_process

        streamlit_process.start_streamlit_process()
        streamlit_process.create_app(app)

    @classmethod
    def _get_env_app_available_port(cls) -> int:
        for port in cls.get_env_app_ports():
            if not cls._port_is_used(port):
                return port

        raise Exception(
            "No available port for the env app, please stop existing app in Settings > Monitoring > Others > Streamlit apps")

    @classmethod
    def _port_is_used(cls, port: int) -> bool:
        return port in [app.port for app in cls.running_processes.values()]

    @classmethod
    def stop_all_processes(cls) -> None:
        for streamlit_process in cls.running_processes.values():
            streamlit_process.stop_process()

        cls.running_processes = {}

    @classmethod
    def stop_process(cls, env_hash: str) -> None:
        if env_hash in cls.running_processes:
            cls.running_processes[env_hash].stop_process()
            del cls.running_processes[env_hash]

    ############################# OTHERS ####################################

    @classmethod
    def get_status_dto(cls) -> StreamlitStatusDTO:
        return StreamlitStatusDTO(
            processes=[process.get_status_dto() for process in cls.running_processes.values()],
        )

    @classmethod
    def get_main_app_port(cls) -> int:
        return Settings.get_streamlit_main_app_port()

    @classmethod
    def get_env_app_ports(cls) -> List[int]:
        return Settings.get_streamlit_env_app_ports()

    @classmethod
    def get_app_full_url(cls, app_id: str) -> str:
        for streamlit_process in cls.running_processes.values():
            if streamlit_process.has_app(app_id):
                return streamlit_process.get_app_full_url(app_id)

        raise Exception(f"App {app_id} not found")

    @classmethod
    def get_app_dir(cls) -> str:
        if cls.app_dir is None:
            cls.app_dir = Settings.make_temp_dir()
        return cls.app_dir
