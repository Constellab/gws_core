# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import pandas
from pandas import DataFrame

class View:
    
    @staticmethod
    def dict_to_table(data: dict, \
                      orient: str='index', dtype=None, \
                      columns=None, stringify:bool=False) -> (str, "DataFrame", ):
        """
        Convert a dictionary to a table. The method `DataFrame.from_dict()` is used. See this method to learn more about conversion
        
        :param data: The dictionary
        :type data: `dict`
        :param orient: The orientation (`index` or `ccolums`). If `index` then each key of the data is a new index (i.e. a new row). Each is a column otherwise.
        :type orient: `str`
        :param dtype: The data type
        :type dtype: see `pandas.DataFrames`
        :param columns: The column names (only valid if `orient=index`)
        :type columns: `List[str]`
        :param stringify: If True, tha table is stringify to a csv string; False otherwise
        :type stringify: `bool`
        :return: The corresponding table as `pandas.DataFrame` or as string
        :rtype: `pandas.DataFrame`, `str`
        """
        
        df = DataFrame.from_dict(data, orient, dtype, columns)
        if stringify:
            return df.to_csv()
        else:
            return df
    

    @staticmethod
    def subsample(table: DataFrame, max_nb_bins:int = 100, orient:str='index', zoom:list=[None, None, None, None], method="smooth", stringify:bool=False)-> (str, "DataFrame", ):
        
        """
        Subsamples a table according to the `index`, `columns` or `both` orientation
        
        :param table: The table
        :type table: `pandas.DataFrame`
        :param max_nb_bins: The maximum number of bins
        :type max_nb_bins: `int`
        :param orient: The subsampling orientation (`index` (default), `columns` or `both`)
        :type orient: `str`
        :param zoom: The zoom region. The values of the index and column limits on which to zoom.
        :type zoom: `list`
        :param method: The subsampling method (`smooth` (default), `random`). If `smooth`, samples are smooth on each bin by computing the average (only valid for numeric values); If `random`, random values are selected in each bin. In any cases, if data are not numeric, all non-numeric values are replaced the first value.
        :type method: `str`
        :param stringify: If True, tha table is stringify to a csv string; False otherwise
        :type stringify: `bool`
        :return: The corresponding table as `pandas.DataFrame` or as string
        :rtype: `pandas.DataFrame`, `str`
        """
        
        if orient == "both":
            df = subsample(table, max_nb_bins=max_nb_bins, orient="index", zoom=zoom, stringify=False)
            df = subsample(df, max_nb_bins=max_nb_bins, orient="columns", zoom=zoom, stringify=False)
        else:
            if orient == "columns":
                nb_bins = table.shape[1]
                orientation_values = table.index.values.tolist()
            else:
                nb_bins = table.shape[0]
                orientation_values = table.columns.values.tolist()
            
            
            if nb_bins > 100:
                bin_size = int(nb_bins / max_nb_bins)
                if bin_size >= 1:
                    for bin_index in range(0,bin_size):
                        # compress the data in the kth bin
                        pass
        
        if stringify:
            return table.to_csv()
        else:
            return df
        