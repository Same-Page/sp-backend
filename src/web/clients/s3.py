import os

import boto3
import botocore

from cfg.s3 import S3_BUCKET


AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY', 'AWS_ACCESS_KEY_missing')
AWS_SECRET_ACCESS_KEY = os.environ.get(
    'AWS_SECRET_ACCESS_KEY', 'AWS_SECRET_ACCESS_KEY_missing')

s3 = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY)


def upload_file(file, file_name, acl="public-read"):

    s3.upload_fileobj(
        file,
        S3_BUCKET,
        file_name,
        ExtraArgs={"ACL": acl, "ContentType": file.content_type},
    )

