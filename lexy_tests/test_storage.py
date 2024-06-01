import datetime
import os
import time
import warnings

import boto3
import pytest
from botocore.client import Config
from botocore.exceptions import ClientError, NoCredentialsError
from google.cloud import storage
from google.oauth2 import service_account

from lexy.storage import signed_url_is_expired
from lexy.storage.client import construct_key_for_document, construct_key_for_thumbnail
from lexy.storage.gcs import GCSClient
from lexy.storage.s3 import S3Client
from lexy.models.document import Document


@pytest.fixture(scope='module')
def s3():
    s3_client = boto3.client('s3')
    try:
        s3_client.list_buckets()
        yield s3_client
    except NoCredentialsError:
        warnings.warn("S3 credentials are not available", UserWarning)
        pytest.skip("S3 credentials are not available")
    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDenied':
            warnings.warn("S3 client access denied", UserWarning)
            pytest.skip("S3 access is denied")
        else:
            warnings.warn(f"S3 client has an error: {e.response}", UserWarning)
            pytest.skip("S3 client has an error")


@pytest.fixture(scope='module')
def s3v4():
    s3v4_client = boto3.client('s3', config=Config(signature_version='s3v4'))
    try:
        s3v4_client.list_buckets()
        yield s3v4_client
    except NoCredentialsError:
        warnings.warn("S3 credentials are not available", UserWarning)
        pytest.skip("S3 credentials are not available")
    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDenied':
            warnings.warn("S3 client access denied", UserWarning)
            pytest.skip("S3 access is denied")
        else:
            warnings.warn(f"S3 client has an error: {e.response}", UserWarning)
            pytest.skip("S3 client has an error")


@pytest.fixture(scope='module')
def gcs(settings):
    credentials_file = settings.GOOGLE_APPLICATION_CREDENTIALS
    if not credentials_file:
        pytest.skip("GOOGLE_APPLICATION_CREDENTIALS is not set")

    print(f"Creating GCS client using credentials file: {credentials_file}")
    credentials = service_account.Credentials.from_service_account_file(credentials_file)
    yield storage.Client(credentials=credentials)


@pytest.fixture(scope='module')
def lx_s3():
    s3_client = S3Client()
    if not s3_client.is_authenticated():
        pytest.skip("S3 client is not authenticated")
    yield s3_client


@pytest.fixture(scope='module')
def lx_s3v4():
    config = Config(signature_version='s3v4')
    s3_client = S3Client(config=config)
    if not s3_client.is_authenticated():
        pytest.skip("S3 client is not authenticated")
    yield s3_client


@pytest.fixture(scope='module')
def lx_gcs(settings):
    credentials_file = settings.GOOGLE_APPLICATION_CREDENTIALS
    if not credentials_file:
        pytest.skip("GOOGLE_APPLICATION_CREDENTIALS is not set")

    gcs_client = GCSClient()
    if not gcs_client.is_authenticated():
        pytest.skip("GCS client is not authenticated")
    yield gcs_client


@pytest.fixture(scope='module')
def test_file_document():
    return 'sample_data/documents/hotd.txt'


@pytest.fixture(scope='module')
def test_s3_object(s3, test_file_document, settings):

    bucket_name = settings.S3_TEST_BUCKET
    object_prefix = settings.COLLECTION_DEFAULT_CONFIG['storage_prefix']
    object_name = os.path.join(object_prefix, 'hotd.txt')

    if not bucket_name:
        pytest.skip("S3_TEST_BUCKET is not set")

    # Upload the test document
    s3.upload_file(test_file_document, bucket_name, object_name)
    print(f"Created test_s3_object: 's3://{bucket_name}/{object_name}'")

    yield bucket_name, object_name

    # Clean up
    s3.delete_object(Bucket=bucket_name, Key=object_name)
    print(f"Deleted test_s3_object: 's3://{bucket_name}/{object_name}'")


@pytest.fixture(scope='module')
def test_gcs_object(gcs, test_file_document, settings):

    bucket_name = settings.GCS_TEST_BUCKET
    object_prefix = settings.COLLECTION_DEFAULT_CONFIG['storage_prefix']
    object_name = os.path.join(object_prefix, 'hotd.txt')

    if not bucket_name:
        pytest.skip("GCS_TEST_BUCKET is not set")

    # Upload the test document
    bucket = gcs.bucket(bucket_name)
    blob: storage.blob.Blob = bucket.blob(object_name)
    with open(test_file_document, 'rb') as file:
        blob.upload_from_file(file)
    print(f"Created test_gcs_object: 'gs://{bucket_name}/{object_name}'")

    yield bucket_name, object_name

    # Clean up
    blob.delete()
    print(f"Deleted test_gcs_object: 'gs://{bucket_name}/{object_name}'")


# TODO: add async tests
class TestStorageClient:
    """Tests for third-party clients."""

    def test_s3_client(self, s3):
        assert s3 is not None
        buckets = s3.list_buckets()
        print(f"s3: {buckets = }")
        assert len(buckets) > 0

    def test_s3v4_client(self, s3v4):
        assert s3v4 is not None
        buckets = s3v4.list_buckets()
        print(f"s3v4: {buckets = }")
        assert len(buckets) > 0

    def test_gcs_client(self, gcs):
        assert gcs is not None
        buckets = list(gcs.list_buckets())
        print(f"gcs: {buckets = }")
        assert len(buckets) > 0

    def test_generate_signed_url_s3(self, s3, test_s3_object):
        bucket_name, object_name = test_s3_object
        expiration = 3

        s3_signed_url = s3.generate_presigned_url('get_object',
                                                  Params={'Bucket': bucket_name, 'Key': object_name},
                                                  ExpiresIn=expiration)
        assert s3_signed_url is not None
        # s3 url can also include the region
        assert s3_signed_url.startswith(f"https://{bucket_name}.s3.")
        assert f".amazonaws.com/{object_name}" in s3_signed_url
        assert signed_url_is_expired(s3_signed_url, svc='Amz') is False
        time.sleep(expiration)
        assert signed_url_is_expired(s3_signed_url, svc='Amz') is True

    def test_generate_signed_url_s3v4(self, s3v4, test_s3_object):
        bucket_name, object_name = test_s3_object
        expiration = 3

        s3v4_signed_url = s3v4.generate_presigned_url('get_object',
                                                      Params={'Bucket': bucket_name, 'Key': object_name},
                                                      ExpiresIn=expiration)
        assert s3v4_signed_url is not None
        # s3 url can also include the region
        assert s3v4_signed_url.startswith(f"https://{bucket_name}.s3.")
        assert f".amazonaws.com/{object_name}" in s3v4_signed_url
        assert signed_url_is_expired(s3v4_signed_url, svc='Amz') is False
        time.sleep(expiration)
        assert signed_url_is_expired(s3v4_signed_url, svc='Amz') is True

    def test_generate_signed_url_gcs(self, gcs, test_gcs_object):
        bucket_name, object_name = test_gcs_object
        expiration = 3

        bucket = gcs.bucket(bucket_name)
        blob: storage.blob.Blob = bucket.blob(object_name)
        gcs_signed_url = blob.generate_signed_url(expiration=datetime.timedelta(seconds=expiration),
                                                  version="v4")
        assert gcs_signed_url is not None
        assert gcs_signed_url.startswith(f"https://storage.googleapis.com/{bucket_name}/{object_name}")
        assert signed_url_is_expired(gcs_signed_url, svc='Goog') is False
        time.sleep(expiration)
        assert signed_url_is_expired(gcs_signed_url, svc='Goog') is True


# TODO: add async tests
class TestLexyStorageClient:
    """Tests for Lexy storage clients (i.e., `lexy.storage.client.StorageClient`)."""

    def test_lx_s3_client(self, lx_s3):
        assert lx_s3 is not None
        buckets = lx_s3.list_buckets()
        print(f"lx_s3: {buckets = }")
        assert len(buckets) > 0

    def test_lx_s3v4_client(self, lx_s3v4):
        assert lx_s3v4 is not None
        buckets = lx_s3v4.list_buckets()
        print(f"lx_s3v4: {buckets = }")
        assert len(buckets) > 0

    def test_lx_gcs_client(self, lx_gcs):
        assert lx_gcs is not None
        buckets = lx_gcs.list_buckets()
        print(f"lx_gcs: {buckets = }")
        assert len(buckets) > 0

    def test_generate_presigned_url_lx_s3(self, lx_s3, test_s3_object):
        bucket_name, object_name = test_s3_object
        expiration = 3

        s3_signed_url = lx_s3.generate_presigned_url(bucket_name, object_name, expiration)
        assert s3_signed_url is not None
        # s3 url can also include the region
        assert s3_signed_url.startswith(f"https://{bucket_name}.s3.")
        assert f".amazonaws.com/{object_name}" in s3_signed_url
        assert signed_url_is_expired(s3_signed_url, svc='Amz') is False
        time.sleep(expiration)
        assert signed_url_is_expired(s3_signed_url, svc='Amz') is True

    def test_generate_presigned_url_lx_s3v4(self, lx_s3v4, test_s3_object):
        bucket_name, object_name = test_s3_object
        expiration = 3

        s3v4_signed_url = lx_s3v4.generate_presigned_url(bucket_name, object_name, expiration)
        assert s3v4_signed_url is not None
        # s3 url can also include the region
        assert s3v4_signed_url.startswith(f"https://{bucket_name}.s3.")
        assert f".amazonaws.com/{object_name}" in s3v4_signed_url
        assert signed_url_is_expired(s3v4_signed_url, svc='Amz') is False
        time.sleep(expiration)
        assert signed_url_is_expired(s3v4_signed_url, svc='Amz') is True

    def test_generate_presigned_url_lx_gcs(self, lx_gcs, test_gcs_object):
        bucket_name, object_name = test_gcs_object
        expiration = 3

        gcs_signed_url = lx_gcs.generate_presigned_url(bucket_name, object_name, expiration)
        assert gcs_signed_url is not None
        assert gcs_signed_url.startswith(f"https://storage.googleapis.com/{bucket_name}/{object_name}")
        assert signed_url_is_expired(gcs_signed_url, svc='Goog') is False
        time.sleep(expiration)
        assert signed_url_is_expired(gcs_signed_url, svc='Goog') is True


class TestConstructStorageKeys:
    """Tests for constructed storage keys."""

    @pytest.mark.asyncio
    async def test_construct_key_for_document_with_document(self):
        document = Document(collection_id="123", document_id="456")
        key = await construct_key_for_document(document=document)
        assert key == "collections/123/documents/456"

    @pytest.mark.asyncio
    async def test_construct_key_for_document_with_collection_and_document_id(self):
        key = await construct_key_for_document(collection_id="123", document_id="456")
        assert key == "collections/123/documents/456"

    @pytest.mark.asyncio
    async def test_construct_key_for_document_with_path_prefix(self):
        document = Document(collection_id="123", document_id="456")
        key = await construct_key_for_document(document=document, path_prefix="public")
        assert key == "public/collections/123/documents/456"

    @pytest.mark.asyncio
    async def test_construct_key_for_document_with_filename(self):
        document = Document(collection_id="123", document_id="456")
        key = await construct_key_for_document(document=document, filename="document.jpg")
        assert key == "collections/123/documents/456/document.jpg"

    @pytest.mark.asyncio
    async def test_construct_key_for_document_without_document_or_ids(self):
        with pytest.raises(ValueError, match="Either a document object or collection_id and document_id must be "
                                             "provided."):
            await construct_key_for_document()

    @pytest.mark.asyncio
    async def test_construct_key_for_thumbnail_with_document(self):
        document = Document(collection_id="123", document_id="456")
        key = await construct_key_for_thumbnail((200, 200), document=document)
        assert key == "collections/123/thumbnails/200x200/456"

    @pytest.mark.asyncio
    async def test_construct_key_for_thumbnail_with_collection_and_document_id(self):
        key = await construct_key_for_thumbnail((200, 200), collection_id="123", document_id="456")
        assert key == "collections/123/thumbnails/200x200/456"

    @pytest.mark.asyncio
    async def test_construct_key_for_thumbnail_with_path_prefix(self):
        document = Document(collection_id="123", document_id="456")
        key = await construct_key_for_thumbnail((200, 200), document=document, path_prefix="public")
        assert key == "public/collections/123/thumbnails/200x200/456"

    @pytest.mark.asyncio
    async def test_construct_key_for_thumbnail_with_filename(self):
        document = Document(collection_id="123", document_id="456")
        key = await construct_key_for_thumbnail((200, 200), document=document, filename="thumbnail.jpg")
        assert key == "collections/123/thumbnails/200x200/456/thumbnail.jpg"

    @pytest.mark.asyncio
    async def test_construct_key_for_thumbnail_without_dims(self):
        document = Document(collection_id="123", document_id="456")
        with pytest.raises(ValueError, match="Thumbnail dimensions must be provided."):
            await construct_key_for_thumbnail(None, document=document)

    @pytest.mark.asyncio
    async def test_construct_key_for_thumbnail_without_document_or_ids(self):
        with pytest.raises(ValueError, match="Either a document object or collection_id and document_id must be "
                                             "provided."):
            await construct_key_for_thumbnail((200, 200))
