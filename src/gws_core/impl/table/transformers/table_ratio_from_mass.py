# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.config.param_spec import BoolParam, StrParam
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.impl.table.helper.table_ratio_helper import TableRatioHelper
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from ..table import Table


@task_decorator(
    unique_name="TableColumnRatioMass",
    human_name="Table column ratio mass",
    short_description="Apply ratio stored in table to another table",
)
class TableColumnRatioMass(Task):
    """
    Task to apply a list of ratio contained in a table to another table. This is useful to apply a lot of ratio.

    The operation column (see ```Ratio operation column``` config) defines operations to apply to the input table.

    **The input table must not contained special caracters in the column names**

    # Examples
    Let's say you have this ```Table``` with the column A, B, C, D
    | A | B  | C  | D  |
    |---|----|----|----|
    | 1 | 10 | 11 | -9 |
    | 2 | 8  | 10 | -6 |
    | 3 | 6  | 9  | -3 |

    Here is few example that you can write in the ```operations``` column.

    * Addition : ```A + B + C```
    * Constant : ```A  + 10```
    * Subtraction : ```A - C```
    * Multiplication : ```A * C```
    * Division : ```A / C```
    * Exponentiation : ```A ** C```
    * Modulus :  ``` A % C```
    * Floor division : ``` A // C```
    * Advanced exemple : ```(A + B) / (C * D)```

    # Comparaison

    This task support comparaison, it will return the string ```True``` or ```False```.

    Comparaison operators : ```==```, ```!=```, ```>```, ```<```, ```>=``` and ```<=```

    ## Math functions

    This task supports basic math functions : ```sin```, ```cos```, ```exp```, ```log```, ```expm1```, ```log1p```, ```sqrt```, ```sinh```, ```cosh```, ```tanh```, ```arcsin```, ```arccos```, ```arctan```, ```arccosh```, ```arcsinh```, ```arctanh```, ```abs```, ```arctan2``` and ```log10```.

    Example : ```log(A)```

    **Only works if  ```Error on unknown column``` is checked**



    # Error on unknown column
    If ```Error on unknown column``` is unchecked, the ratio will not fail on unknow columns (replace with 0) but only basic operations and comparaison are supported (no funcions).

    If ```Error on unknown column``` is checked, the ratio will fail on unknow columns (raise an exception) but it supports all operations.


    """

    input_specs: InputSpecs = {
        'table':
        InputSpec(
            Table, human_name='Input table',
            short_description='Table that contains the data to apply ratio on'),
        'ratio_table':
        InputSpec(
            Table, human_name='Ratio table',
            short_description='Table that contains the ratio name and operations')}
    output_specs: OutputSpecs = {'target': OutputSpec(Table)}

    config_specs: ConfigSpecs = {
        'ratio_name_column':
        StrParam(
            optional=True, human_name='Ratio name column',
            short_description='Name of the column in Ratio Table that contains ratio names. If not provided, the first column will be used'),
        'ratio_operation_column':
        StrParam(
            optional=True, human_name='Ratio operation column',
            short_description='Name of the column in Ratio Table that contains ratio operations. If not provided, the second column will be used'),
        'error_on_unknown_column':
        BoolParam(
            default_value=False, human_name='Error on unknown column',
            short_description='If true, an error will be raised if a column is not found. If false, the column will be replace by 0.',
            visibility='protected')}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        table: Table = inputs['table']
        ratio_table: Table = inputs['ratio_table']

        if ratio_table.nb_columns != 2:
            raise BadRequestException(
                "The ratio table must have exactly 2 columns, the first column contains the name of the ratio, the second column contains the ratio values")

        result = TableRatioHelper.columns_ratio_from_table(
            table, ratio_table.get_data(),
            ratio_name_column=params.get('ratio_name_column'),
            ratio_operation_column=params.get('ratio_operation_column'),
            error_on_unknown_column=params.get('error_on_unknown_column'))
        return {'target': result}
