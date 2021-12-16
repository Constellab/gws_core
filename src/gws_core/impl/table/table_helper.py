
from typing import List


class TableHelper:

    CSV_DELIMITERS: List[str] = ['\t', ',', ';']

    @classmethod
    def detect_csv_delimiter(cls, csv_str: str) -> str:
        """Method to guess the delimiter of a csv string based on delimiter count
        """
        if csv_str is None or len(csv_str) < 10:
            return None

        max_delimiter: str = None
        max_delimiter_count: int = 0

        # use a sub csv to improve speed
        sub_csv = csv_str[0:10000]

        for delimiter in cls.CSV_DELIMITERS:
            count: int = sub_csv.count(delimiter)
            if(count > max_delimiter_count):
                max_delimiter = delimiter
                max_delimiter_count = count

        return max_delimiter
