# This is a snippet template for a Python live task.
import os

import pandas

# Do the job here ...
data = pandas.read_csv(source_path, header=0, sep=';')

# remove column named 'one'
result = data.drop(columns=['one'])

# Write the output file in the target folder
result.to_csv(os.path.join(target_folder, "result.csv"), index=False)
