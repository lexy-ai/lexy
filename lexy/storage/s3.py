import logging

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from lexy.storage.base import StorageClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class S3Client(StorageClient):

    def __init__(self, **kwargs):
        logger.info("Creating S3 client")
        self.client = boto3.client('s3', **kwargs)

    def is_authenticated(self) -> bool:
        try:
            self.client.list_buckets()
            return True
        except NoCredentialsError:
            return False
        except ClientError:
            return False
        except Exception:
            raise

    def list_buckets(self) -> list[str]:
        response = self.client.list_buckets()
        return [bucket['Name'] for bucket in response['Buckets']]

    def upload_object(self, fileobj, bucket_name: str, object_name: str, rewind: bool = True) -> dict:
        if isinstance(fileobj, str):
            with open(fileobj, 'rb') as f:
                fileobj = f
        else:
            if rewind:
                fileobj.seek(0)
        self.client.upload_fileobj(fileobj, bucket_name, object_name)
        # FIXME: refactor
        return {
            "storage_service": "s3",
            "s3_bucket": bucket_name,
            "s3_key": object_name,
            # "s3_url": f"https://{bucket_name}.s3.amazonaws.com/{object_name}",
            # "s3_uri": f"s3://{bucket_name}/{object_name}",
        }

    def generate_presigned_url(self, bucket_name: str, object_name: str, expiration: int = 3600) -> str:
        url = self.client.generate_presigned_url('get_object',
                                                 Params={
                                                     'Bucket': bucket_name,
                                                     'Key': object_name
                                                 },
                                                 ExpiresIn=expiration)
        return url

    def delete_object(self, bucket_name: str, object_name: str) -> None:
        self.client.delete_object(Bucket=bucket_name, Key=object_name)
