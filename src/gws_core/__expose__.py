# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from .impl.csv.csv_process import CSVExporter, CSVImporter, CSVTable


def doc():
    return """
    This brick contains core GWS modules

    Utilites
    ========
    * CSV module
    * JSON module
    """


def name():
    return "Core library"


def title():
    return "This is the core library"


def tree():
    return {
        ":CSV": {
            "doc": "",
            ":Data": {
                "doc": "",
                ":CSVData": {
                    "doc": "",
                    "type": CSVTable,
                },
            },
            ":Process": {
                "doc": "",
                ":CSVImporter": {
                    "doc": "",
                    "type": CSVImporter,
                },
                ":CSVExporter": {
                    "doc": "",
                    "type": CSVExporter,
                }
            },
        }
    }
