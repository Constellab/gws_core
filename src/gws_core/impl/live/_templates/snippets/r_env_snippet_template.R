# This is a snippet template for a R live task.

library("argparse")

# Initialize the argument parser
# Here, we suppose that the code is called using a shell command "file.R --datapath ./filepath"
parser <- ArgumentParser(description='Read the shell arguments')
parser$add_argument('--datapath', dest='datapath', help='The input data path')

# Parse arguments
args <- parser$parse_args()
datapath <- args$datapath

# Do the job here ...
table = read.csv(datapath)

# Write the output file
# Please ensure that the path of this file is set in the list of `output file paths` of the form to caputure it in the outputs of the tasks.
write.csv(table,"result.csv", row.names = TRUE)