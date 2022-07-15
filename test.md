You can provided multiple values to replace. It also supports regex. If multiple values are provided,
there are replaced sequentially, so the second replace can rewrite the first replace.
The table's tags are kept.

For each configuration, if ```Is regex``` is checked, the ```search value``` is considerer as a regex and there is no modification to it.
Otherwise the ```search value``` is converted (see ```Convertion```). The ```replace value``` is always converted.

### Convertion
The params values supports 2 special values:
- ```NaN```: convert to NaN
- ```None```: convert to None

If the value is someting else, the system tries to convert it to a ```number```. If this is convertible to a ```number``` the system will use the ```number```, otherwise the value is kept as is.

