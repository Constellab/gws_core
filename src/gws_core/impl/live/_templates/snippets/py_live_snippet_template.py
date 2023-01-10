# This is a snippet template for a python live task.

# HOW TO?
# Three variables are reserved in a python live task
# - params: a dictionary containing the parameters
# - inputs: a dictionnary containing the input data defined by the key 'source'
# - outputs: a dictionnary used to define the output result through the key 'target'

# Declare brick & package dependencies (recommended)
#!require:pip pandas
#!require:brick gws_core==4.1


from gws_core import Table
from pandas import DataFrame

# Read parameters
a = params['a']
b = params['b']

# Get the input data
table = inputs['source']

# Do the job here ...
df = DataFrame({'column1': [1, a], 'column2': [0, b]})
df = df + table.get_data()
result = Table(data=df)

# Send the final result to the output
outputs = {'target': result}
