from typing import TYPE_CHECKING

import boto3

from lexy.core.config import settings

if TYPE_CHECKING:
    from lexy.models.document import Document


async def get_s3_client() -> boto3.client:
    client_kwargs = {}
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY.get_secret_value()
    if settings.AWS_REGION:
        client_kwargs["region_name"] = settings.AWS_REGION
    return boto3.client('s3', **client_kwargs)


def generate_presigned_urls_for_document(document: "Document",
                                         s3_client: boto3.client = None,
                                         expiration: int = 3600) -> dict:
    """ Generate presigned URLs for a document.

    Args:
        document (Document): The document object.
        s3_client: The S3 client.
        expiration (int): The number of seconds the presigned URLs are valid for. Default is 3600 seconds (1 hour).

    Returns:
        Dict: A dictionary containing presigned URLs.

    Examples:
        >>> from lexy_py import LexyClient
        >>> lx = LexyClient()
        >>> my_image_document = lx.list_documents(collection_name='my_image_collection', limit=1)[0]
        >>> generate_presigned_urls_for_document(my_image_document, s3_client=s3_client)
        {
            "object": "https://my-bucket.s3.amazonaws.com/path/to/object?...",
            "thumbnails": {
                "256x256": "https://my-bucket.s3.amazonaws.com/path/to/thumbnail?..."
            }
        }
        >>> my_pdf_document = lx.list_documents(collection_name='pdf_collection', limit=1)[0]
        >>> generate_presigned_urls_for_document(my_pdf_document, s3_client=s3_client)
        {
            "object": "https://my-bucket.s3.amazonaws.com/path/to/object?...",
        }
    """
    presigned_urls = {}

    # url for the document object
    if document.meta.get('s3_bucket') and document.meta.get('s3_key'):
        presigned_urls["object"] = (
            s3_client.generate_presigned_url('get_object',
                                             Params={'Bucket': document.meta['s3_bucket'],
                                                     'Key': document.meta['s3_key']},
                                             ExpiresIn=expiration))

    # urls for thumbnails
    if document.meta.get('image') and document.meta.get('image').get('thumbnails'):
        presigned_urls["thumbnails"] = {}
        for dims, vals in document.meta.get('image').get('thumbnails').items():
            presigned_urls["thumbnails"][dims] = (
                s3_client.generate_presigned_url('get_object',
                                                 Params={'Bucket': vals.get('s3_bucket'),
                                                         'Key': vals.get('s3_key')},
                                                 ExpiresIn=expiration))

    return presigned_urls


async def construct_key_for_document(document: "Document" = None, collection_id: str = None, document_id: str = None,
                                     path_prefix: str = None, filename: str = None) -> str:
    """ Construct an S3 key for a document.

    Args:
        document (Document): The document object.
        collection_id (str): The collection ID.
        document_id (str): The document ID.
        path_prefix (str): The path prefix.
        filename (str): The filename.

    Returns:
        str: The S3 key.

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
        raise ValueError("Either a document object or collection_id and document_id must be provided.")
    if path_prefix:
        key = f"{path_prefix.rstrip('/')}/{key}"
    if filename:
        key = f"{key}/{filename}"
    return key


async def construct_key_for_thumbnail(dims: tuple[int, int], document: "Document" = None, collection_id: str = None,
                                      document_id: str = None, path_prefix: str = None, filename: str = None) -> str:
    """ Construct an S3 key for thumbnails of a document.

    Args:
        dims (tuple[int, int]): The dimensions of the thumbnail.
        document (Document): The document object.
        collection_id (str): The collection ID.
        document_id (str): The document ID.
        path_prefix (str): The path prefix.
        filename (str): The filename.

    Returns:
        str: The S3 key.

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
        ...                             document_id='123456', filename='thumb.jpg')
        'collections/423c718b/thumbnails/150x150/123456/thumb.jpg'
        >>> construct_key_for_thumbnail(dims=(200, 200), document=my_image_document, path_prefix='public')
        'public/collections/423c718b/thumbnails/200x200/123456'
    """
    if not dims:
        raise ValueError("Thumbnail dimensions must be provided.")
    if document and document.collection_id and document.document_id:
        key = f"collections/{document.collection_id}/thumbnails/{dims[0]}x{dims[1]}/{document.document_id}"
    elif collection_id and document_id:
        key = f"collections/{collection_id}/thumbnails/{dims[0]}x{dims[1]}/{document_id}"
    else:
        raise ValueError("Either a document object or collection_id and document_id must be provided.")
    if path_prefix:
        key = f"{path_prefix.rstrip('/')}/{key}"
    if filename:
        key = f"{key}/{filename}"
    return key


def upload_file_to_s3(file, s3_client: boto3.client, s3_bucket: str, s3_key: str, rewind: bool = True) -> dict:
    """ Upload a file to S3.

    Args:
        file: The file to upload.
        s3_client (boto3.client): The S3 client.
        s3_bucket (str): The name of the S3 bucket.
        s3_key (str): The S3 key for the file.
        rewind (bool): Whether to rewind the file object before uploading. Default is True.

    Returns:
        Dict: A dictionary containing the S3 bucket, key, URL, and URI.
    """
    if rewind:
        file.seek(0)
    s3_client.upload_fileobj(file, s3_bucket, s3_key)
    return {
        "s3_bucket": s3_bucket,
        "s3_key": s3_key,
        "s3_url": f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}",
        "s3_uri": f"s3://{s3_bucket}/{s3_key}",
    }
