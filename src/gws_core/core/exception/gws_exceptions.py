# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum


class GWSException(Enum):
    INTERNAL_SERVER_ERROR = "Internal server error"
    WRONG_CREDENTIALS = "Wrong email or password"
    WRONG_CREDENTIALS_INVALID_API_KEY = "Not authorized. Invalid API key"
    WRONG_CREDENTIALS_USER_NOT_FOUND = "Not authorized. Cannot generate user access token. User not found"
    WRONG_CREDENTIALS_USER_NOT_ACTIVATED = "Not authorized. Cannot generate user access token. User not active"
    INVALID_TOKEN = "Not authorized. Invalid token"
    FUNCTIONALITY_UNAVAILBLE_IN_PROD = "This functionnality is not available in the production environment"
    MISSING_PROD_API_URL = "Missing production API URL"
    ERROR_DURING_DEV_LOGIN = "Error during login in development environment"
    CENTRAL_API_DEV_DISABLED = "The centrals routes are disabled in dev"
    OBJECT_URI_NOT_FOUND = "{{objectName}} with uri : '{{id}}' not found"
    USER_NOT_ACTIVATED = "User not activated"
    RESOURCE_NOT_COMPATIBLE = "Trying to set an incompatible resource to port '{{port}}'. Resource type: '{{resource_type}}', excepted types : '{{expected_types}}'."
    MISSING_CONFIG_PARAMS = "The mandatory configs '{{config_names}}' are missing."
    EXPERIMENT_RUN_EXCEPTION = "{{error}} {{context}} | Experiment : '{{experiment}}'"
    PROCESS_BUILD_EXCEPTION = "{{error}} | Process : '{{instance_name}}'"
    PROTOCOL_BUILD_EXCEPTION = "{{error}} | Protocol : '{{instance_name}}'"
    MISSING_INPUT_RESOURCES = "The inputs '{{port_names}}' were not provided but are mandatory"
    IMCOMPATIBLE_PORT = "Invalid connection, port are imcompatible. The output '{{out_port_name}}' types ({{out_port_types}}) can't be converted to input '{{in_port_name}}' types ({{in_port_types}})"
    EXPERIMENT_STOPPED_MANUALLY = "Experiment manually stopped by a user."
