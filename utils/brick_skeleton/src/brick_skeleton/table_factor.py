
from pandas import DataFrame

from gws_core import (ConfigParams, InputSpec, IntParam, OutputSpec, Table,
                      Task, TaskInputs, TaskOutputs, task_decorator)


@task_decorator("TableFactor", human_name="Table factor",
                short_description="Apply a factor to a table")
class TableFactor(Task):
    """
    Apply a factor to a table. This is the solution for the tutorial on 'Create your first task' :
    https://constellab.community/bricks/gws_core/latest/latest/doc/tutorials/create-your-first-task

    """

    input_specs = {'input_table': InputSpec(Table, human_name="Table",
                                            short_description="The input table")}
    output_specs = {'output_table': OutputSpec(Table, human_name="Result",
                                               short_description="The output table")}

    config_specs = {"factor": IntParam(human_name='Factor',
                                       short_description="Factor to apply to the table")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        # retrive the input table
        input_table: Table = inputs['input_table']

        # retrieve the factor param value
        factor: int = params['factor']

        # get dataframe from the table
        input_df: DataFrame = input_table.get_data()

        # apply the factor
        output_df = input_df * factor

        # create the output table from the dataframe
        output_table = Table(output_df)

        # return the output table
        return {'output_table': output_table}
