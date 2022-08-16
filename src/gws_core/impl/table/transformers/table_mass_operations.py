# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.config.param_spec import BoolParam, StrParam
from gws_core.impl.table.helper.table_operation_helper import \
    TableOperationHelper
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from ..table import Table


@task_decorator(
    unique_name="TableColumnMassOperations",
    human_name="Table column operation mass",
    short_description="Apply operations stored in table to another table",
)
class TableColumnMassOperations(Task):
    """
    Task to apply a list of operation contained in a table to another table. This is useful to apply a lot of operations.

    The ```Calculation column``` config defines operations to apply to the input table.

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
    If ```Error on unknown column``` is unchecked, the operation will not fail on unknow columns (the result for operations with unknown column will be 'NaN') but only basic operations and comparaison are supported (no functions).

    If ```Error on unknown column``` is checked, the operation will fail on unknow columns (raise an exception) but it supports all operations.
    """

    input_specs: InputSpecs = {
        'table':
        InputSpec(
            Table, human_name='Input table',
            short_description='Table that contains the data to apply operations on'),
        'operation_table':
        InputSpec(
            Table, human_name='Operation table',
            short_description='Table that contains the operation\'s name and operations\'s calculations')}
    output_specs: OutputSpecs = {'target': OutputSpec(Table)}

    config_specs: ConfigSpecs = {
        'name_column':
        StrParam(
            optional=True, human_name='Name column',
            short_description='Name of the column in Operation Table that contains operations\' names. If not provided, the first column will be used'),
        'calculations_column':
        StrParam(
            optional=True, human_name='Calculations column',
            short_description='Name of the column in Operation Table that contains operations\' calculations. If not provided, the second column will be used'),
        'keep_original_columns':
        BoolParam(
            default_value=False, human_name='Keep original columns',
            short_description="If true, the original columns of the Table will be added at the end of the Table. If false, only the calculcation columns are kept.",
            visibility='protected'),
        'error_on_unknown_column':
        BoolParam(
            default_value=False, human_name='Error on unknown column',
            short_description="If true, an error will be raised if a column is not found. If false, the result will be 'NaN'.",
            visibility='protected')}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        table: Table = inputs['table']
        operation_table: Table = inputs['operation_table']

        result = TableOperationHelper.column_mass_operations(
            table, operation_table.get_data(),
            operation_name_column=params.get('name_column'),
            operation_calculations_column=params.get('calculations_column'),
            error_on_unknown_column=params.get('error_on_unknown_column'),
            keep_original_columns=params.get('keep_original_columns'),
        )
        return {'target': result}
