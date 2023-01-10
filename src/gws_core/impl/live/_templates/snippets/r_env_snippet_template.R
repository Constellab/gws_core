# This is a snippet template for a R live task.

print("Hello, world!")
d <- read.table(text=
'Name     Month  Rate1     Rate2
Aira       0      12        23
Aira       0      12        23
Aira       0      12        23
Ben        1      10        4
Ben        2      8         2
Cat        1      3        18
Cat        1      6        0
Cat        1      0        0', header=TRUE)
table = aggregate(d[, 3:4], list(d$Name), mean)
write.csv(table,"table.csv", row.names = TRUE)