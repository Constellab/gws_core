# This is a snippet template for a python live task.
# This code is executed in the same context as the run method of a Task.
# This mean you can import brick or packages and call method of the Task object.

# HOW TO?
# 2 variables are reserved in a python live task
# - source: resource set as input of the task
# - target: fill this variable with the output (resource) of the task


# Import modules
from gws_core import Table

# access task method to log a messages
self.log_info_message('Transposing table')
# Transpose the input table
table: Table = source[0].transpose()

# set the new table a output or the live task
target = [table]
