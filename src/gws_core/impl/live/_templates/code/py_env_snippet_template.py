# This is a snippet template for a Python live task.
import pandas

# Do the job here ...
data = pandas.read_csv(source_paths[0], header=0, index_col=0, sep=',')

# transform the data
result = data.transpose()

# Write the output file in the target folder
result_path = "result.csv"
result.to_csv(result_path, index=True)
target_paths = [result_path]
