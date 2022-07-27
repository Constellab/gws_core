Transformer to extract values of tags into in new rows that are appended to the end of the table.

Multiple tag keys can be provided to extract multiple tags (one row is created by tag key).

## Example
Let's say you have the following table, the first row does not really exist in the table, it is just to show the tags of the columns.

| A          | B          |
|------------|------------|
| Gender : M | Gender : F |
| 1          | 5          |
| 2          | 6          |
| 3          | 7          |
| 4          | 8          |

Here is the result of the extraction of the ```Gender``` tag.

| A          | B          |
|------------|------------|
| Gender : M | Gender : F |
| 1          | 5          |
| 2          | 6          |
| 3          | 7          |
| 4          | 8          |
| M          | F          |

A new row is created containing the values of the ```Gender``` tag.

## Parameters

- The ```New row name``` parameter allows you to define the names newly create rows that contains tags
- The ```Tag values type```` parameters allows you to force the convertion of the tag values. 
  - Use ```numeric``` to convert the tag values to float.
  - User ```char``` to keep the tag values as strings.