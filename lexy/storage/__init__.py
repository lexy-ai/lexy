from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse


def presigned_url_is_expired(url, storage_service: str = 's3') -> bool:
    if storage_service == 's3':
        return s3_presigned_url_is_expired(url)
    elif storage_service == 'azure':
        raise NotImplementedError
    elif storage_service == 'gcs':
        raise NotImplementedError
    else:
        raise ValueError(f'Unsupported storage service: {storage_service} - '
                         f'must be one of the following: s3, azure, gcs')


def s3_presigned_url_is_expired(url) -> bool:
    query = parse_qs(urlparse(url).query)
    if 'X-Amz-Expires' in query:
        expiration = query['X-Amz-Expires'][0]
        expiration = int(expiration)
        expiration = timedelta(seconds=expiration)
        expiration = datetime.now() + expiration
        return expiration < datetime.now()
    elif 'Expires' in query:
        expiration = query['Expires'][0]
        expiration = int(expiration)
        expiration = datetime.fromtimestamp(expiration)
        return expiration < datetime.now()
    else:
        raise ValueError('No expiration found in presigned url')
