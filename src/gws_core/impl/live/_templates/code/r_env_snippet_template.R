# This is a snippet template for a R live task.

# Read the source csv file
csv <- read.csv(source_path, header = TRUE, sep = ",")

# Transpose the table
csv_result <- t(csv)

# Write the csv file into the result folder
write.csv(csv_result, file = paste(target_folder, "/result.csv", sep = ""), row.names = FALSE)