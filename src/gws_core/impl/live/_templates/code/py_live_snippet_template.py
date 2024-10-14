# This is a snippet template for a python agent.
# This code is executed in the same context as the run method of a Task.
# This mean you can import brick or packages and call method of the Task object.

# HOW TO?
# 2 variables are reserved in a python agent
# - sources: array containing the input resource
# - targets: array that must be filled with output resources


# Import modules
from gws_core import Table

# access task method to log a messages
self.log_info_message('Transposing table')
# Transpose the input table
table: Table = sources[0].transpose()

# set the new table a output or the agent
targets = [table]
