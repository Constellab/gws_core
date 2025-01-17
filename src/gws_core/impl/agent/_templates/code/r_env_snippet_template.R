# This is a snippet template for a R agent.

# Read the source csv file with header, row names and comma separator
csv <- read.csv(source_paths[1], header = TRUE, sep = ",", row.names = 1)

# Transpose the table, keep the header
csv_result <- t(csv)

# Write the csv file into the result folder
result_path <- "result.csv"
write.csv(csv_result, file = result_path, row.names = TRUE, col.names = TRUE)
target_paths <- c(result_path)
