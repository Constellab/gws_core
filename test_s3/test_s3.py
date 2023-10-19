
from typing import List, Optional

import botocore.auth
import botocore.credentials
import uvicorn
from botocore.awsrequest import AWSRequest
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.requests import Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing_extensions import Annotated

app = FastAPI()

# In-memory storage for storing objects
object_store = {}

object_metadata = {
    "example-bucket/object-key-1": {"Content-Type": "text/plain", "Content-Length": "123"},
    "example-bucket/object-key-2": {"Content-Type": "image/jpeg", "Content-Length": "456"},
}

# Simulated user access keys (replace with your actual user management)
access_keys = {
    "your_access_key_id": "your_secret_access_key",
}


# @app.middleware("http")
async def add_process_time_header(request: Request, call_next):

    # Parse the Authorization header to obtain AWS access key, request date, and signature
    access_key, request_date, region_name, service_name, signature = parse_authorization_header(request.headers.get(
        'Authorization'))

    if access_key not in access_keys:
        raise HTTPException(status_code=403, detail="Access Denied")

    secret_key = access_keys[access_key]

    # Create a botocore.auth.HmacV1 instance
    # Create SigV4Auth instance
    credentials = botocore.credentials.Credentials(access_key, secret_key)
    auth = botocore.auth.SigV4Auth(credentials, service_name, region_name)

    # header = {'User-Agent': 'Boto3/1.26.142 Python/3.8.10 Linux/5.10.16.3-microsoft-standard-WSL2 Botocore/1.29.165'}
    headers = {'x-amz-date': request.headers.get('x-amz-date'),
               'x-amz-content-sha256': request.headers.get('x-amz-content-sha256'),
               'host': request.headers.get('host')}
    if request.headers.get('content-md5'):
        headers['content-md5'] = request.headers.get('content-md5')
    request_2 = AWSRequest(method=request.method, url=str(request.url), headers=headers, data=b'')
    request_2.context["payload_signing_enabled"] = True  # payload signing is not supported
    request_2.context["timestamp"] = request.headers.get('x-amz-date')

    # Generate the canonical request
    canonical_request = auth.canonical_request(request_2)

    # # Generate the string to sign
    string_to_sign = auth.string_to_sign(request_2, canonical_request)

    # Calculate the expected signature
    expected_signature = auth.signature(string_to_sign, request_2)

    if signature != expected_signature:
        raise HTTPException(status_code=403, detail="Access Denied")
    response = await call_next(request)

    return response


def parse_authorization_header(authorization_header):
    # Parse the Authorization header to obtain AWS access key, request date, region, service, and signature
    parts = authorization_header.split(", ")
    access_key = parts[0].split("Credential=")[1].split("/")[0]
    request_date = parts[0].split("Credential=")[1].split("/")[1].split("/")[0]
    region = parts[0].split("Credential=")[1].split("/")[2]
    service = parts[0].split("Credential=")[1].split("/")[3]
    signature = parts[2].split("Signature=")[1]
    return access_key, request_date, region, service, signature


class S3Object(BaseModel):
    key: str
    data: str


@app.put("/s3/{bucket}/{key}")
async def upload_object(request: Request):
    form_data = await request.form()
    form_data_dict = dict(form_data)
    # body = await request.body()
    # print(body)
    # return empty response 204 status, otherwise the client expect an XML
    response = Response(status_code=204)
    return response


@app.get("/s3/{bucket}/{key}")
def download_object(bucket: str, key: str):
    # print('WWWWWWWWWW 2')
    # object_store_key = f"{bucket}/{key}"
    # if object_store_key not in object_metadata:
    #     raise HTTPException(status_code=404, detail="Object not found")
    # object_data = object_metadata[object_store_key]
    # print(object_data)
    # return {"data": object_data}
    return FileResponse('/lab/user/bricks/gws_core/settings.json', media_type='application/json', filename='test.json')


@app.get("/s3/{bucket}")
def list_objects(bucket: str):
    objects_in_bucket = [key for key in object_store.keys() if key.startswith(bucket + "/")]
    return {"objects": objects_in_bucket}


@app.head("/s3/{bucket}/{key}")
def head_object(bucket: str, key: str):
    print('WWWWWWWWWW')
    object_store_key = f"{bucket}/{key}"
    if object_store_key not in object_metadata:
        raise HTTPException(status_code=404, detail="Object not found")
    object_data = object_metadata[object_store_key]
    return {"data": object_data}


uvicorn.run(app, host='0.0.0.0', port=8080)
