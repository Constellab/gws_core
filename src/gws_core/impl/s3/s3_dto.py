# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional, TypedDict


class BucketObjectOwner(TypedDict):
    ID: str
    DisplayName: str


class BucketObject(TypedDict):
    Key: str
    LastModified: str
    ETag: str
    Size: int
    Owner: BucketObjectOwner
    StorageClass: str


class ListBucketResult(TypedDict):
    Name: str
    Prefix: str
    Marker: str
    MaxKeys: int
    IsTruncated: bool  # true if all the results were not returned
    # if IsTruncated is true, this element is present and its value is the marker to use in the next request
    NextMarker: Optional[str]
    Contents: List[BucketObject]
