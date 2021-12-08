# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.impl.table.table import Table
from gws_core.task.transformer.transformer_decorator import \
    transformer_decorator

from ....config.param_spec import BoolParam, IntParam, ListParam, StrParam
from ....task.task import Task
from ...file.file import File

# ####################################################################
#
# TableScaler class
#
# ####################################################################


@transformer_decorator(
    unique_name="TableScaler",
    resource_type=Table,
    short_description="Scales the numeric values of the table",
)
class TableScaler(Task):
    pass
