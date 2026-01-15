import os
from enum import Enum

from gws_core.core.utils.logger import Logger


class ExecutionContext(Enum):
    """Execution context of the application.

    This enum represents the different execution contexts in which the application can run.
    The execution context is determined by the GWS_EXECUTION_CONTEXT environment variable
    and helps the application adapt its behavior based on where it's running.
    """

    # Main execution context - default context for backend/server operations
    MAIN = "MAIN"

    # Reflex web application context - when running as a Reflex app
    REFLEX = "REFLEX"

    # Streamlit web application context - when running as a Streamlit app
    STREAMLIT = "STREAMLIT"

    @classmethod
    def is_app_context(cls) -> bool:
        """Check if the current execution context is a web application context.

        Returns:
            bool: True if running in REFLEX or STREAMLIT context, False otherwise (MAIN context)
        """
        execution_context = cls.get_execution_context()
        return execution_context in {ExecutionContext.REFLEX, ExecutionContext.STREAMLIT}

    @classmethod
    def get_os_env_name(cls) -> str:
        """Get the name of the OS environment variable that stores the execution context.

        Returns:
            str: The environment variable name "GWS_EXECUTION_CONTEXT"
        """
        return "GWS_EXECUTION_CONTEXT"

    @classmethod
    def get_execution_context(cls) -> "ExecutionContext":
        """Get the current execution context from the environment variable.

        Reads the GWS_EXECUTION_CONTEXT environment variable and returns the corresponding
        ExecutionContext enum value. If the environment variable is not set or contains
        an invalid value, defaults to MAIN context.

        Returns:
            ExecutionContext: The current execution context (MAIN, REFLEX, or STREAMLIT)
        """
        env_value = os.environ.get(cls.get_os_env_name(), "MAIN").upper()
        try:
            return ExecutionContext(env_value)
        except ValueError:
            Logger.error(f"Invalid execution context: {env_value}, defaulting to MAIN")
            return ExecutionContext.MAIN
