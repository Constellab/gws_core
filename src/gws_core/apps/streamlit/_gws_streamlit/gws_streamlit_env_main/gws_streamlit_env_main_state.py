"""State class for registering GWS Streamlit virtual environment apps."""

from gws_streamlit_base import StreamlitMainStateBase


class StreamlitEnvMainState(StreamlitMainStateBase):
    """State manager for GWS Streamlit apps in virtual environment mode."""

    @classmethod
    def _post_initialize(cls):
        """No post-initialization needed for virtual environment apps."""
        pass

    @classmethod
    def register_streamlit_env_app(cls) -> None:
        """
        Register and initialize a GWS Streamlit app running in a virtual environment.

        This calls StreamlitBootstrap.initialize() and returns source_paths (not loaded resources)
        for apps that run in isolated virtual environments with custom dependencies.

        Usage in user's main.py:
        ```python
        from gws_streamlit_env_main import StreamlitEnvAppState

        source_paths, params = StreamlitEnvAppState.register_streamlit_env_app()

        # Your Streamlit app code here
        st.title("My Virtual Env App")
        ```
        """
        # Initialize bootstrap (no return value)
        cls.initialize()

    @classmethod
    def get_source_paths(cls) -> list[str]:
        """Return source paths from app config."""
        config = cls.get_app_config()
        return config.get("source_ids", [])
