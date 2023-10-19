import boto3
import requests

# Configure the S3 client
s3_client = boto3.client(
    's3',
    region_name='us-east-1',
    endpoint_url='http://localhost:8080/s3',  # Replace with your local server's URL
    aws_access_key_id='your_access_key_id',  # Replace with appropriate access key
    aws_secret_access_key='your_secret_access_key',  # Replace with appropriate secret key
)

a = s3_client.upload_file('/lab/user/bricks/gws_core/setup.py', 'super', 'hellopy')
# aa = s3_client.download_file('example-bucket', 'object-key-2', '/lab/user/bricks/gws_core/ttttt.py')
# with open('/lab/user/bricks/gws_core/setup.py', "rb") as f:
# s3_client.upload_fileobj(f, "super", "hellopy")

print(a)
