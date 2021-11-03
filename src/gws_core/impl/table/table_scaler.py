# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...config.param_spec import BoolParam, IntParam, StrParam, ListParam
from ...task.task_decorator import task_decorator
from ..file.file import File
from ...task.task import Task

# ####################################################################
#
# TableScaler class
#
# ####################################################################

@task_decorator(unique_name="TableScaler")
class TableScaler(Task):
    pass
