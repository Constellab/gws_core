

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
    SPACE_API_DEV_DISABLED = "The space's routes are disabled in dev"
    OBJECT_ID_NOT_FOUND = "{{objectName}} with id : '{{id}}' not found"
    USER_NOT_ACTIVATED = "User not activated"
    RESOURCE_NOT_COMPATIBLE = "Trying to set an incompatible resource to port '{{port}}'. Resource type: '{{resource_type}}', excepted types : '{{expected_types}}'."
    MISSING_CONFIG_PARAMS = "The mandatory configs '{{param_names}}' are missing."
    MISSING_CONFIG_PARAM = "The mandatory config '{{param_name}}' is missing."
    UNKNOWN_CONFIG_PARAMS = "The parameter '{{param_name}}' does not exist in the config."
    INVALID_PARAM_VALUE = "Invalid value '{{param_value}}' for the parameter '{{param_name}}'. Error : {{error}}"
    EXPERIMENT_RUN_EXCEPTION = "{{error}} | Experiment : '{{experiment}}'"
    TASK_BUILD_EXCEPTION = "{{error}} | Task : '{{instance_name}}'"
    PROTOCOL_BUILD_EXCEPTION = "{{error}} | Protocol : '{{instance_name}}'"
    MISSING_INPUT_RESOURCES = "The inputs '{{port_names}}' were not provided but are mandatory"
    IMCOMPATIBLE_PORT = "Invalid connection, port are imcompatible. The output '{{out_port_name}}' types {{out_port_types}} can't be converted to input '{{in_port_name}}' types {{in_port_types}}"
    EXPERIMENT_ERROR_BEFORE_RUN = "Error before running the experiment."
    TASK_CHECK_BEFORE_STOP = "Check before task returned false. Reason: {{message}}"
    EXPERIMENT_VALIDATE_RUNNING = "Can't validate a running experiment"
    RESET_ERROR_RESOURCE_USED_IN_ANOTHER_EXPERIMENT = "Can't reset the experiment because the output resource '<a href=\"{{resource_url}}\">{{resource_model_name}}</a>' is used in experiment '<a href=\"{{experiment_url}}\">{{experiment}}</a>'"
    DELETE_GENERATED_RESOURCE_ERROR = "This resource was generatd by a task, it cannot be deleted. Only imported resource can be deleted"
    RESOURCE_USED_ERROR = "This resource is used in the experiment '{{experiment}}', it can't be modified nor deleted"
    INVALID_UNIQUE_CODE = "Not authorized. Invalid url"
    INVALID_LINKED_RESOURCE = "The resource generated on port {{port_name}} is linked to another resource which is not a input of the task. This break the tracability."
    REPORT_VALIDATED = "The report can't be updated not delete because it is validated"
    REPORT_EXP_ALREADY_LINKED = "The experiment is already linked with the report"
    REPORT_VALIDATION_EXP_NOT_VALIDATED = "The linked experiment '{{title}}' must be validated first"
    REPORT_VALIDATION_EXP_OTHER_PROJECT = "The linked experiment '{{title}}' is associated to another project"
    REPORT_VALIDATION_RESOURCE_GENERATED_VIEW_OTHER_EXP = "The view '{{view_name}}' is from the experiment '{{exp_title}}' but this experiment is not linked to the report. Please link this experiment to the report."
    REPORT_VALIDATION_RESOURCE_UPLOADED_VIEW_OTHER_EXP = "The view '{{view_name}}' is from the resource '{{resource_name}}' but this resource is not used by any of the related experiment of the report."
    REPORT_ADD_EXP_OTHER_PROJECT = "Can't link the experiment to the report because they are in different projects"
    REPORT_HAS_A_VIEW_FROM_EXPERIMENT = "Can't dissociate the experiment from the report because the report has a view of a resource that was generated by the experiment"
    EMPTY_FILE = "The file '{{filename}}' is empty"
    INVALID_FILE_ON_UPLOAD = "The file is invalid. Error : '{{error}}'"
    INVALID_FOLDER_ON_UPLOAD = "The folder is invalid. Error : '{{error}}'"
    REPORT_NO_LINKED_EXPERIMENT = "The report is not linked with an experiment. Please link it to an experiment to access views."
    DELETE_PROJECT_WITH_EXPERIMENTS = "The project can't be deleted because it contains synced experiments"
    DELETE_PROJECT_WITH_REPORTS = "The project can't be deleted because it contains synced reports"
    EXP_CONTINUE_LAB_INCOMPATIBLE = "The experiment cannot be continued because the lab version has changed since last execution. Please reset the experiment first."
    PROCESS_UPDATE_RUNNING_ERROR = "The process is running. Please stop the process or wait for it to finish before modifying it."
    PROCESS_UPDATE_FISHINED_ERROR = "The process is finished. Please reset the process before modifying it."
    RESET_ERROR_EXP_LINKED_TO_IN_ANOTHER_EXP = "Can't reset the experiment because one of the output resource is used in experiment '<a href=\"{{experiment_url}}\" target=\"_blank\">{{experiment}}</a>'"
    RESET_ERROR_EXP_LINKED_TO_A_REPORT = "Can't reset the experiment because one of the output resource is used in report '<a href=\"{{report_url}}\" target=\"_blank\">{{report}}</a>'"
    IOFACE_CONNECTED_TO_PARENT_DELETE_ERROR = "The {{ioface_type}} '{{ioface_name}}' is connected in the parent protocol '{{parent_protocol_name}}', please remove the link connected to this {{ioface_type}} in the parent protocol."
    TYPING_NOT_FOUND = "Can't find the typing {{unique_name}} for {{object_type}} in brick {{brick_name}}. Is the brick {{brick_name}} correctly loaded ?"
