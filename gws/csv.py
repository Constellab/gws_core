# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from pathlib import Path
import pandas
from pandas import DataFrame
import numpy as np

from .resource import Resource
from .logger import Error
from .file import *

class CSVData(Resource):
    _required_column_names = []

    def __init__(self, *args, table: (DataFrame, np.ndarray,) = None, \
                 column_names=None, row_names=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not table is None:
            if isinstance(table, DataFrame):
                self.kv_store['table'] = table
            elif isinstance(table, (np.ndarray,list)):
                df = DataFrame(table)
                if column_names:
                    df.columns = column_names
                if row_names:
                    df.index = row_names
                self.kv_store['table'] = df
            else:
                raise Error("CSVData", "__init__", "The table mus be an instance of DataFrame or Numpy array")
    
    # -- A --
 
    # -- C --

    @property
    def column_names(self) -> list:
        """ 
        Returns the column names of the Datatable.

        :return: The list of column names or `None` is no column names exist
        :rtype: list or None
        """

        try:
            return self.table.columns.values.tolist()
        except Exception as _:
            return None

    def column_exists(self, name, case_sensitive=True) -> bool:
        if case_sensitive:
            return name in self.column_names
        else:
            lower_names = [ x.lower() for x in self.column_names ]
            return name.lower() in lower_names

    # -- D --
    
    @property
    def dataframe(self) -> DataFrame:
        """ 
        Returns the inner pandas DataFrame

        :return: The inner DataFrame
        :rtype: pandas.DataFrame
        """
        
        return self.kv_store['table']
    
    @property
    def table(self) -> DataFrame:
        """ 
        Alias of method `dataframe`
        """
        return self.kv_store['table']
    
    # -- E --
    
    def _export(self, file_path: str, delimiter: str="\t", index=True, file_format:str = None, **kwargs):
        """ 
        Export to a repository

        :param file_path: The destination file path
        :type file_path: File
        """
        
        file_extension = Path(file_path).suffix
        if file_extension in [".xls", ".xlsx"] or file_format in [".xls", ".xlsx"] :
            self.table.to_excel(file_path)
        elif file_extension in [".csv", ".tsv", ".txt", ".tab"] or file_format in [".csv", ".tsv", ".txt", ".tab"] :
            self.table.to_csv(
                file_path,
                sep = delimiter,
                index = index
            )
        else:
            raise Error("CSV", "CSVData", "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")
    
    # -- F --
    
    @classmethod
    def from_dict( cls, table: dict, orient='index', dtype=None, columns=None ) -> 'CSVData':
        df = DataFrame.from_dict(table, orient, dtype, columns)
        return cls(table=df)

    # -- G --
    
    def get_column(self, column_name: str, rtype='list') -> ('DataFrame', list):
        if rtype == 'list':
            return list(self.table[column_name].values)
        else:
            return self.table[[column_name]]
        
    # -- H --

    def head(self, n=5) -> DataFrame:
        """ 
        Returns the first n rows for the columns ant targets.

        :param n: Number of rows
        :param n: int
        :return: The `panda.DataFrame` objects representing the n first rows of the `table`
        :rtype: pandas.DataFrame
        """

        return self.table.head(n)

    # -- I --

    @classmethod
    def _import(cls, file_path: str, delimiter: str="\t", header=0, index_col=None, file_format:str = None, **kwargs) -> any:
        """ 
        Import from a repository

        :param file_path: The source file path
        :type file_path: File
        :returns: the parsed data
        :rtype any
        """

        file_extension = Path(file_path).suffix
        if file_extension in [".xls", ".xlsx"] or file_format in [".xls", ".xlsx"] :
            df = pandas.read_excel(file_path)
        elif file_extension in [".csv", ".tsv", ".txt", ".tab"] or file_format in [".csv", ".tsv", ".txt", ".tab"] :
            df = pandas.read_table(
                file_path, 
                sep = delimiter,
                header = header,
                index_col = index_col
            )
        else:
            raise Error("CSVData", "_import", "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")
        return cls(table=df)
    
    # -- J --
    
    @classmethod
    def _join(cls, *args, **params) -> 'Model':
        """ 
        Join several resources

        :param params: Joining parameters
        :type params: dict
        """
        
        #@ToDo: ensure that this method is only called by an Joiner
        
        pass

    
    # -- N --

    @property
    def nb_columns(self) -> int:
        """ 
        Returns the number of columns.

        :return: The number of columns 
        :rtype: int
        """

        return self.table.shape[1]
    
    @property
    def nb_rows(self) -> int:
        """ 
        Returns the number of rows.

        :return: The number of rows 
        :rtype: int
        """

        return self.table.shape[0]

    # -- R --
    
    @property
    def row_names(self) -> list:
        """ 
        Returns the row names.

        :return: The list of row names
        :rtype: list
        """

        return self.table.index.values.tolist()
    
    def _render__as_csv(self, **kwargs):
        """
        Renders the model as a JSON string or dictionnary. This method is used by :class:`ViewModel` to create view rendering.
        
        :param kwargs: Parameters passed to the method :meth:`to_json`.
        :type kwargs: `dict`
        :return: The view representation
        :rtype: `dict`, `str`
        """
        
        return self.to_csv( stringify=True, **kwargs )
    
    # -- S --
 
    def _select(self, **params) -> 'Model':
        """ 
        Select a part of the resource

        :param params: Extraction parameters
        :type params: dict
        """
        
        #@ToDo: ensure that this method is only called by an Selector
        
        pass
    
    def __str__(self):
        return self.table.__str__()
    
    # -- T --
    
    def to_json(self, stringify: bool=False, prettify: bool=False, **kwargs):
        _json = super().to_json(**kwargs)
        _json["data"]["content"] = self.table.to_json()
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
        
    def to_table(self):
        return self.table
        
    def to_csv(self, **kwargs):
        return self.table.to_csv()

    # -- V ---
        
# ####################################################################
#
# Importer class
#
# ####################################################################
    
class CSVImporter(FileImporter):
    input_specs = {'file' : File}
    output_specs = {'data': CSVData}
    config_specs = {
        'file_format': {"type": str, "default": ".csv", 'description': "File format"},
        'delimiter': {"type": 'str', "default": '\t', "description": "Delimiter character. Only for parsing CSV files"},
        'header': {"type": 'int', "default": None, "description": "Row number to use as the column names. Use None to prevent parsing column names. Only for parsing CSV files"},
        'index' : {"type": 'int', "default": None, "description": "Column number to use as the row names. Use None to prevent parsing row names. Only for parsing CSV files"},
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

class CSVExporter(FileExporter):
    input_specs = {'data': CSVData}
    output_specs = {'file' : File}
    config_specs = {
        'file_name': {"type": str, "default": 'file.csv', 'description': "Destination file name in the store"},
        'file_format': {"type": str, "default": ".csv", 'description': "File format"},
        'delimiter': {"type": 'str', "default": "\t", "description": "Delimiter character. Only for parsing CSV files"},
        'header': {"type": bool, "default": True, "description":  "Write column names (header)"},
        'index': {"type": bool, "default": True, 'description': "Write row names (index)"},
        'file_store_uri': {"type": str, "default": None, 'description': "URI of the file_store where the file must be exported"},
    }

# ####################################################################
#
# Loader class
#
# ####################################################################

class CSVLoader(FileLoader):
    input_specs = {}
    output_specs = {'data' : CSVData}
    config_specs = {
        'file_path': {"type": str, "default": None, 'description': "Location of the file to import"},
        'file_format': {"type": str, "default": ".csv", 'description': "File format"},
        'delimiter': {"type": 'str', "default": '\t', "description": "Delimiter character. Only for parsing CSV files"},
        'header': {"type": 'int', "default": None, "description": "Row number to use as the column names. Use None to prevent parsing column names. Only for parsing CSV files"},
        'index' : {"type": 'int', "default": None, "description": "Column number to use as the row names. Use None to prevent parsing row names. Only for parsing CSV files"},
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################

class CSVDumper(FileDumper):
    input_specs = {'data' : CSVData}
    output_specs = {}
    config_specs = {
        'file_path': {"type": str, "default": None, 'description': "Destination of the exported file"},
        'file_format': {"type": str, "default": ".csv", 'description': "File format"},
        'delimiter': {"type": 'str', "default": "\t", "description": "Delimiter character. Only for parsing CSV files"},
        'header': {"type": bool, "default": True, "description":  "Write column names (header)"},
        'index': {"type": bool, "default": True, 'description': "Write row names (index)"},
    }
    


