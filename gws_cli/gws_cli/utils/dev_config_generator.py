import json
import os
from typing import Any

from gws_core import BaseModelDTO

DEV_CONFIG_FILE = "dev_config.json"


class AppDevConfig(BaseModelDTO):
    """Pydantic model representing the structure of dev_config.json"""

    app_dir_path: str = ""
    source_ids: list[str] = []
    params: dict[str, Any] = {}
    env_type: str = "NONE"
    env_file_path: str = ""
    is_reflex_enterprise: bool = False
    is_streamlit_v2: bool = False
    dev_user_email: str | None = ""
    # Access mode to simulate in dev mode: "AUTHENTICATED" (default, uses the system /
    # dev user) or "PUBLIC" (no authentication, simulates a public prod app).
    access_mode: str = "AUTHENTICATED"


def create_dev_config_json(
    app_folder: str,
    is_reflex_enterprise: bool = False,
    is_streamlit_v2: bool = False,
    env_type: str = "NONE",
    env_file_path: str = "",
) -> None:
    """
    Create a dev_config.json file at the specified app path.

    :param app_path: Path where the dev_config.json file should be created
    :param is_reflex_enterprise: Whether this is for a Reflex Enterprise app
    :param is_streamlit_v2: Whether this app uses the Streamlit v2 app API
    :param env_type: Virtual environment type ("NONE", "PIP", "CONDA" or "MAMBA")
    :param env_file_path: Path to the environment file, relative to the app folder
    """
    # Create the dev config object
    dev_config = AppDevConfig(
        params={"param_name": "Value from dev_config.json"},
        is_reflex_enterprise=is_reflex_enterprise,
        is_streamlit_v2=is_streamlit_v2,
        env_type=env_type,
        env_file_path=env_file_path,
    )

    # Write the JSON file
    dev_config_path = os.path.join(app_folder, DEV_CONFIG_FILE)
    with open(dev_config_path, "w", encoding="utf-8") as f:
        json.dump(dev_config.to_json_dict(), f, indent=4)
