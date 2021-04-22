# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import pandas
from pandas import DataFrame

class View:
    
    @staticmethod
    def dict_to_table(table: dict, orient='index', dtype=None, columns=None, stringify:bool=False) -> (str, "DataFrame", ):
        df = DataFrame.from_dict(table, orient, dtype, columns)
        if stringify:
            return df.to_csv()
        else:
            return df
        