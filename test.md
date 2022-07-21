
For earch filters, the system will keep the columns where the value in the row provided by the parameter ```Row name``` validated condition (the ```comparator``` with the ```value``` parameter).The result table will have the same number of rows as the input table.

The ```Row name``` supports pattern. This means that multiple rows can be used in the filter. In this 
case all the values in the provided rows must validate the condition. You can set the value ```*``` in the ```Row name``` which mean that all the values in the column must validate the condition.

Supported operators : ```=```, ```!=```, ```contains```, ```startwith``` and ```endswith```.

If you need to apply filters on text values, you can use the ```Table column data text filter``` task.