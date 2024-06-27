from typing import TYPE_CHECKING, Union

from lexy.core.config import settings
from lexy.storage.base import StorageClient
from lexy.storage.gcs import GCSClient, GoogleCredentialsError
from lexy.storage.s3 import S3Client

if TYPE_CHECKING:
    from lexy.models.document import Document, DocumentBase


# TODO: Add caching
# TODO: Add argument for storage service and default to settings.DEFAULT_STORAGE_SERVICE
# TODO: Move this to lexy.api.deps?
async def get_storage_client() -> StorageClient | None:
    if settings.DEFAULT_STORAGE_SERVICE == "s3":
        # The boto3 client allows for initialization without credentials
        s3_client = S3Client()
        yield s3_client
    elif settings.DEFAULT_STORAGE_SERVICE == "gcs":
        # The google-cloud-storage client requires credentials
        try:
            gcs_client = GCSClient()
            yield gcs_client
        except GoogleCredentialsError:
            yield None
    else:
        raise ValueError("Unsupported storage service configured")


def generate_signed_urls_for_document(
    document: Union["Document", "DocumentBase"],
    storage_client: StorageClient,
    expiration: int = 3600,
) -> dict:
    """Generate signed URLs for a document.

    Args:
        document (Document): The document object.
        storage_client (StorageClient): The storage client.
        expiration (int): The number of seconds the presigned URLs are valid for. Default is 3600 seconds (1 hour).

    Returns:
        Dict: A dictionary containing presigned URLs.

    Examples:
        >>> from lexy_py import LexyClient
        >>> lx = LexyClient()
        >>> my_image_document = lx.list_documents(collection_name='my_image_collection', limit=1)[0]
        >>> generate_signed_urls_for_document(my_image_document, storage_client=storage_client)
        {
            "object": "https://my-bucket.s3.amazonaws.com/path/to/object?...",
            "thumbnails": {
                "256x256": "https://my-bucket.s3.amazonaws.com/path/to/thumbnail?..."
            }
        }
        >>> my_pdf_document = lx.list_documents(collection_name='pdf_collection', limit=1)[0]
        >>> generate_signed_urls_for_document(my_pdf_document, storage_client=storage_client)
        {
            "object": "https://my-bucket.s3.amazonaws.com/path/to/object?...",
        }
    """
    presigned_urls = {}

    # url for the document object
    if document.meta.get("storage_bucket") and document.meta.get("storage_key"):
        presigned_urls["object"] = storage_client.generate_presigned_url(
            bucket_name=document.meta.get("storage_bucket"),
            object_name=document.meta.get("storage_key"),
            expiration=expiration,
        )

    # urls for thumbnails
    if document.meta.get("image") and document.meta.get("image").get("thumbnails"):
        presigned_urls["thumbnails"] = {}
        for dims, vals in document.meta.get("image").get("thumbnails").items():
            presigned_urls["thumbnails"][dims] = storage_client.generate_presigned_url(
                bucket_name=vals.get("storage_bucket"),
                object_name=vals.get("storage_key"),
                expiration=expiration,
            )

    return presigned_urls


async def construct_key_for_document(
    document: "Document" = None,
    collection_id: str = None,
    document_id: str = None,
    path_prefix: str = None,
    filename: str = None,
) -> str:
    """Construct a storage key (object name) for a document.

    Args:
        document (Document): The document object.
        collection_id (str): The collection ID.
        document_id (str): The document ID.
        path_prefix (str): The path prefix.
        filename (str): The filename.

    Returns:
        str: The storage key (object name).

    Raises:
        ValueError: If neither a document object nor collection_id and document_id are provided.

    Examples:
        >>> from lexy_py import LexyClient
        >>> lx = LexyClient()
        >>> my_image_document = lx.list_documents(collection_name='my_image_collection', limit=1)[0]
        >>> construct_key_for_document(my_image_document)
        'collections/423c718b/documents/123456'
        >>> construct_key_for_document(collection_id='423c718b', document_id='123456')
        'collections/423c718b/documents/123456'
        >>> construct_key_for_document(collection_id='423c718b', document_id='123456', filename='image.jpg')
        'collections/423c718b/documents/123456/image.jpg'
        >>> construct_key_for_document(document=my_image_document, path_prefix='public')
        'public/collections/423c718b/documents/123456'
    """
    if document and document.collection_id and document.document_id:
        key = f"collections/{document.collection_id}/documents/{document.document_id}"
    elif collection_id and document_id:
        key = f"collections/{collection_id}/documents/{document_id}"
    else:
        raise ValueError(
            "Either a document object or collection_id and document_id must be provided."
        )
    if path_prefix:
        key = f"{path_prefix.rstrip('/')}/{key}"
    if filename:
        key = f"{key}/{filename}"
    return key


async def construct_key_for_thumbnail(
    dims: tuple[int, int],
    document: "Document" = None,
    collection_id: str = None,
    document_id: str = None,
    path_prefix: str = None,
    filename: str = None,
) -> str:
    """Construct a storage key (object name) for thumbnails of a document.

    Args:
        dims (tuple[int, int]): The dimensions of the thumbnail.
        document (Document): The document object.
        collection_id (str): The collection ID.
        document_id (str): The document ID.
        path_prefix (str): The path prefix.
        filename (str): The filename.

    Returns:
        str: The storage key (object name).

    Raises:
        ValueError: If neither a document object nor collection_id and document_id are provided.

    Examples:
        >>> from lexy_py import LexyClient
        >>> lx = LexyClient()
        >>> my_image_document = lx.list_documents(collection_name='my_image_collection', limit=1)[0]
        >>> construct_key_for_thumbnail(dims=(200, 200), document=my_image_document)
        'collections/423c718b/thumbnails/200x200/123456'
        >>> construct_key_for_thumbnail(dims=(200, 200), collection_id='423c718b', document_id='123456')
        'collections/423c718b/thumbnails/200x200/123456'
        >>> construct_key_for_thumbnail(dims=(150, 150), collection_id='423c718b',
        ...                             document_id='123456', filename='thumbnail.jpg')
        'collections/423c718b/thumbnails/150x150/123456/thumbnail.jpg'
        >>> construct_key_for_thumbnail(dims=(200, 200), document=my_image_document, path_prefix='public')
        'public/collections/423c718b/thumbnails/200x200/123456'
    """
    if not dims:
        raise ValueError("Thumbnail dimensions must be provided.")
    if document and document.collection_id and document.document_id:
        key = f"collections/{document.collection_id}/thumbnails/{dims[0]}x{dims[1]}/{document.document_id}"
    elif collection_id and document_id:
        key = (
            f"collections/{collection_id}/thumbnails/{dims[0]}x{dims[1]}/{document_id}"
        )
    else:
        raise ValueError(
            "Either a document object or collection_id and document_id must be provided."
        )
    if path_prefix:
        key = f"{path_prefix.rstrip('/')}/{key}"
    if filename:
        key = f"{key}/{filename}"
    return key
