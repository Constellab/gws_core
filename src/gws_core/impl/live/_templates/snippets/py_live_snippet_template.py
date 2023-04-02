# This is a snippet template for a python live task.

# HOW TO?
# Three variables are reserved in a python live task
# - params: a dictionary containing the parameters
# - inputs: a dictionnary containing the input data defined by the key 'source'
# - outputs: a dictionnary used to define the output result through the key 'target'

# Declare brick & package dependencies (recommended)
#!require:pip pandas
#!require:brick gws_core==4.1

# Import modules
from gws_core import Table
from gws_core import PackageHelper as pkg
from pandas import DataFrame

# Check a module exists
pkg.module_exists("pandas")         # returns True
pkg.module_exists("my_pip_module")  # returns False
# Install a pip package and load the module
pkg.install("my-pip-package")
my_module = pkg.load_module("my_pip_module")  # command 'import my_pip_module' should alwo work

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
