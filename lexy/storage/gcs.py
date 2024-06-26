import datetime
import logging

from google.cloud import storage
from google.oauth2 import service_account
from google.auth.exceptions import DefaultCredentialsError

from lexy.core.config import settings
from lexy.storage.base import StorageClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GoogleCredentialsError(Exception):
    """Raised when missing credentials file."""
    pass


class GCSClient(StorageClient):

    def __init__(self, credentials_file: str = settings.GOOGLE_APPLICATION_CREDENTIALS, **kwargs):
        if credentials_file:
            logger.info(f"Creating GCS client using credentials file: {credentials_file}")
            credentials = service_account.Credentials.from_service_account_file(credentials_file)
        else:
            raise GoogleCredentialsError("Missing credentials file for Google Cloud Storage. Make sure to set "
                                         "`GOOGLE_APPLICATION_CREDENTIALS` to a valid JSON file containing "
                                         "service account credentials.")
        self.client = storage.Client(credentials=credentials, **kwargs)

    def is_authenticated(self) -> bool:
        try:
            self.client.list_buckets(max_results=1)
            return True
        except DefaultCredentialsError:
            return False
        except Exception:
            raise

    def list_buckets(self) -> list[str]:
        buckets = self.client.list_buckets()
        return [bucket.name for bucket in buckets]

    def upload_object(self, fileobj, bucket_name: str, object_name: str, rewind: bool = True) -> dict:
        bucket = self.client.bucket(bucket_name)
        blob: storage.blob.Blob = bucket.blob(object_name)
        if isinstance(fileobj, str):
            blob.upload_from_filename(fileobj)
        else:
            blob.upload_from_file(fileobj, rewind=rewind)
        return {
            "storage_service": "gcs",
            "storage_bucket": bucket_name,
            "storage_key": object_name,
            # "storage_url": f"https://storage.googleapis.com/{bucket_name}/{object_name}",
            # "storage_uri": f"gs://{bucket_name}/{object_name}",
        }

    def generate_presigned_url(self, bucket_name: str, object_name: str, expiration: int = 3600) -> str:
        bucket = self.client.bucket(bucket_name)
        blob: storage.blob.Blob = bucket.blob(object_name)
        url = blob.generate_signed_url(expiration=datetime.timedelta(seconds=expiration),
                                       version="v4")
        return url

    def delete_object(self, bucket_name: str, object_name: str) -> None:
        bucket = self.client.bucket(bucket_name)
        blob: storage.blob.Blob = bucket.blob(object_name)
        blob.delete()
