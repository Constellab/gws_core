# This is a snippet template for a python live task.

# HOW TO?
# 2 variables are reserved in a python live task
# - source: resource set as input of the task
# - output: fill this variable with the output (resource) of the task


# Import modules
from gws_core import Table

# Transpose the input table
table: Table = source.transpose()

target = table
