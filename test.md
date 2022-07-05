Transformer to unfold table rows based on provided tags.

For each columns, the transformer will unfold the rows based on the provided tags.
This means that the unfolder will create a new column for each tags combinaison.

The generated column names are the concatenation of the orginial column name along with tag values.

This task copies the orignial columns tags to the result columns. 

## Examples
Let's say you havet the following table, the column row_tags does not really exist in the table, 
it is just to show the tags of the rows

| row_tags                 | A | B |
|--------------------------|---|---|
| Gender : M <br> Age : 10 | 1 | 5 |
| Gender : F <br> Age : 10 | 2 | 6 |
| Gender : F <br> Age : 10 | 3 | 7 |
| Gender : M <br> Age : 20 | 4 | 8 |

### Unfold with 1 tag

Here is the result if you unfold by the tag ```Gender```

| A_M | B_M | A_F | B_F |
|-----|-----|-----|-----|
| 1   | 5   | 2   | 6   |
| 4   | 8   | 3   | 7   |

If 1 tag key is provided, for 1 column, it will create a new column for each tag values (here ```M``` and ```F```) and fill this column
with the base column values that are tagged with the value.

The orginial column name is change (from ```A``` to ```'A_M``` for example) but a new tag is add to each column containing the orignial column name. The key of the tag is configurable with the ```Tag key column name``` params (default to ```column_name```) and the value is the orinal column name. For the column ```A_M``` that new tag will be ```column_name:A```

### Unfold with multiple tags

Here is the result if you unfold by the tags ```Gender``` and ```Age```

| A_M_10 | B_M_10 | A_M_20 | B_M_20 | A_F_10 | B_F_10 |
|--------|--------|--------|--------|--------|--------|
| 1      | 5      | 4      | 8      | 2      | 6      |
|        |        |        |        | 3      | 7      |

If multiple tag keys are provided, it will create a new column for each tag values combination (here ```M-10```,  ```M-20```,  ```F-10``` and  ```F-20```) and fill this column
with the base column values that are tagged with combination of tag values.
