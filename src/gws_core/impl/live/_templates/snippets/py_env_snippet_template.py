# This is a snippet template for a Python live task.

import sys

from gws_core import File, TableImporter
from pandas import DataFrame

# Parse the input arguments
# Here, we suppose that the code is called using a shell command "file.py --data ./path1 --out ./path2"
for k, val in enumerate(sys.argv):
    if val == "--data":  # <- path of the input data
        data_path = sys.argv[k+1]
    elif val == "--out":  # <- path of the output data
        output_file_path = sys.argv[k+1]


# Do the job here ...
table = TableImporter.call(File(path=data_path))
df: DataFrame = table.get_data()
df = df * 2

df.to_csv(output_file_path)
