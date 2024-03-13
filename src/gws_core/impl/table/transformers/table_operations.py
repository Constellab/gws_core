
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import BoolParam, ListParam
from gws_core.impl.table.helper.table_operation_helper import \
    TableOperationHelper

from ....task.transformer.transformer import Transformer, transformer_decorator
from ..table import Table


@transformer_decorator(
    unique_name="TableColumnOperations",
    resource_type=Table,
    short_description="Operations on columns for a table",
)
class TableColumnOperations(Transformer):
    """

    This task allows you to do mathematical operation on a Table column.

    It works with the column names, supports basic operations, comparator, parenthesis and some math functions.

    ## Examples
    Let's say you have this ```Table``` with the column A, B, C, D
    | A | B  | C  | D  |
    |---|----|----|----|
    | 1 | 10 | 11 | -9 |
    | 2 | 8  | 10 | -6 |
    | 3 | 6  | 9  | -3 |

    Here is few example that you can write in the ```operations``` config.

    * Addition : ```A + B + C```
    * Constant : ```A  + 10```
    * Subtraction : ```A - C```
    * Multiplication : ```A * C```
    * Division : ```A / C```
    * Exponentiation : ```A ** C```
    * Modulus :  ``` A % C```
    * Floor division : ``` A // C```
    * Advanced exemple : ```(A + B) / (C * D)```

    ## Comparaison

    This task support comparaison, it will return the string ```True``` or ```False```.

    Comparaison operators : ```==```, ```!=```, ```>```, ```<```, ```>=``` and ```<=```

    ## Math functions

    This task supports basic math functions : ```sin```, ```cos```, ```exp```, ```log```, ```expm1```, ```log1p```, ```sqrt```, ```sinh```, ```cosh```, ```tanh```, ```arcsin```, ```arccos```, ```arctan```, ```arccosh```, ```arcsinh```, ```arctanh```, ```abs```, ```arctan2``` and ```log10```.

    Example : ```log(A)```


    ## Define column names
    You can define a custom column name in the ```operations```. Example : ```E = A + B```, this will set the result in the ```E``` columns.

    ## Multiple operation
    Multiple operation are possible but it requires an assignment to a new columns.

    For exemple, if you want to create 2 new calculated columns you could do write 2 operation (in 2 different lines) :
    ```
    E = A + B
    F = C - D
    ```

    The result of the previous operation can also be use for the next operation (here we use the new column ```E``` to calculate ```F```) :
    ```
    E = A + B
    F = E - D
    ```


    ## Advanced usage

    This task uses the eval function of python dataframe. To see all the possibility, check the following link : https://pandas.pydata.org/pandas-docs/stable/user_guide/enhancingperf.html#expression-evaluation-via-eval

    """

    config_specs: ConfigSpecs = {
        "operations": ListParam(human_name="Operations", short_description="Operations on columns, see documentation for more info"),
        'keep_original_columns':
        BoolParam(
            default_value=False, human_name='Keep original columns',
            short_description="If true, the original columns of the Table will be added at the end of the Table. If false, only the calculcation columns are kept.",
        )
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        return TableOperationHelper.column_operations(source, params["operations"], params["keep_original_columns"])
