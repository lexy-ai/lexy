from typing import TYPE_CHECKING

import boto3

from lexy.core.config import settings

if TYPE_CHECKING:
    from lexy.models.document import Document


async def get_s3_client() -> boto3.client:
    client_kwargs = {}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    if settings.aws_region:
        client_kwargs["region_name"] = settings.aws_region
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
        >>> lexy = LexyClient()
        >>> my_image_document = lexy.list_documents('my-image-collection', limit=1)[0]
        >>> generate_presigned_urls_for_document(my_image_document, s3_client=s3_client)
        {
            "object": "https://my-bucket.s3.amazonaws.com/path/to/object?...",
            "thumbnails": {
                "256x256": "https://my-bucket.s3.amazonaws.com/path/to/thumbnail?..."
            }
        }
        >>> my_pdf_document = lexy.list_documents('pdf-collection', limit=1)[0]
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