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


def create_dev_config_json(app_folder: str, is_reflex_enterprise: bool = False) -> None:
    """
    Create a dev_config.json file at the specified app path.

    :param app_path: Path where the dev_config.json file should be created
    :param is_reflex_enterprise: Whether this is for a Reflex Enterprise app
    """
    # Create the dev config object
    dev_config = AppDevConfig(
        params={"param_name": "Value from dev_config.json"},
        is_reflex_enterprise=is_reflex_enterprise,
    )

    # Write the JSON file
    dev_config_path = os.path.join(app_folder, DEV_CONFIG_FILE)
    with open(dev_config_path, "w", encoding="utf-8") as f:
        json.dump(dev_config.to_json_dict(), f, indent=4)
