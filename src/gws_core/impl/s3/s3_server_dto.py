from typing import List

from mypy_boto3_s3.type_defs import TagTypeDef
from typing_extensions import TypedDict


class S3TagSet(TypedDict):
    """Type corresponding to the S3 TagSet used in XML
    """
    Tag: List[TagTypeDef]


class S3GetTagResponse(TypedDict):
    VersionId: str
    TagSet: S3TagSet
    ResponseMetadata: None


class S3UpdateTagRequest(TypedDict):
    TagSet: S3TagSet
