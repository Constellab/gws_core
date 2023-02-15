# This is a snippet template for a Python live task.

import sys
import argparse

from pandas import DataFrame

# Initialize the argument parser
# Here, we suppose that the code is called using a shell command "file.py --datapath ./filepath"
parser = argparse.ArgumentParser(description='Read the shell arguments')
parser.add_argument('--datapath', dest='datapath', help='The input data path')

# Parse arguments
args = parser.parse_args()
datapath = args.datapath

# Do the job here ...
data = pandas.read_csv(datapath)

# Write the output file
# Please ensure that the path of this file is set in the list of `output file paths` of the form to caputure it in the outputs of the tasks.
data.to_csv("result.csv")
